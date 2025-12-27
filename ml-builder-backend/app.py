# app.py
import os
import uuid
import re
import pickle
from typing import Optional
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from joblib import dump

from ml_models.preprocessing import PreprocessorFactory, PreprocessConfig
from ml_models.classifiers import (
    PerceptronModel,
    DecisionTreeModel,
    MLPBackpropModel,
)


app = Flask(__name__)
CORS(app)  # allow React frontend to call the API

os.makedirs("saved_models", exist_ok=True)

# In-memory "session" store.
# For a real deployment you'd move this to Redis / DB.
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Redis client (optional). If `REDIS_URL` is set in the environment we will
# persist sessions to Redis so they survive process/container restarts.
redis_client: Optional["redis.Redis"] = None
USE_REDIS = False
if os.environ.get("REDIS_URL"):
    try:
        import redis

        redis_client = redis.from_url(os.environ["REDIS_URL"])
        USE_REDIS = True
    except Exception:
        # If redis import/connection fails we fall back to in-memory only.
        redis_client = None
        USE_REDIS = False


# Helper functions

def get_session(session_id: str) -> Dict[str, Any]:
    # First check local in-memory cache
    if session_id in SESSIONS:
        return SESSIONS[session_id]

    # Fall back to Redis if configured
    if USE_REDIS and redis_client is not None:
        key = f"session:{session_id}"
        raw = redis_client.get(key)
        if raw:
            try:
                sess = pickle.loads(raw)
                # Populate in-memory cache for faster subsequent access
                SESSIONS[session_id] = sess
                return sess
            except Exception:
                # Corrupt entry — treat as missing
                pass

    raise KeyError("Invalid session_id. Upload a dataset first.")


def _persist_session(session_id: str, sess: Dict[str, Any]):
    """Persist session to Redis if enabled (also keep in-memory copy)."""
    SESSIONS[session_id] = sess
    if USE_REDIS and redis_client is not None:
        key = f"session:{session_id}"
        try:
            redis_client.set(key, pickle.dumps(sess))
        except Exception:
            app.logger.exception("Failed to persist session to Redis")


# 1) Upload dataset

@app.route("/api/upload", methods=["POST"])
def upload_dataset():
    """
    Expects: multipart/form-data with a 'file' field (.csv or Excel)
    Returns: preview (first 5 rows), num_rows, num_cols, columns
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part named 'file' in request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file."}), 400

    filename = file.filename.lower()
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            # read as Excel by default if not CSV
            df = pd.read_excel(file)
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {e}"}), 400

    # Create new session
    session_id = str(uuid.uuid4())
    sess = {
        "dataframe": df,
        "preprocess_config": None,
        "preprocessor": None,
        "models": {},  # model_type -> { pipeline, metrics }
    }
    _persist_session(session_id, sess)

    preview_rows = df.head(5).to_dict(orient="records")
    num_rows, num_cols = df.shape

    return jsonify(
        {
            "session_id": session_id,
            "preview": preview_rows,
            "num_rows": int(num_rows),
            "num_cols": int(num_cols),
            "columns": list(df.columns),
        }
    )


# 2) Select pre-processing

@app.route("/api/preprocess", methods=["POST"])
def preprocess_data():
    """
    JSON body:
    {
      "session_id": "...",
      "method": "normalization" | "onehot",
      "target_column": "label"
    }
    """
    data = request.get_json(force=True)
    try:
        session_id = data["session_id"]
        method = data["method"]
        target_column = data["target_column"]
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400

    try:
        sess = get_session(session_id)
        df = sess["dataframe"]

        config: PreprocessConfig = PreprocessorFactory.analyze_dataframe(df, target_column)
        preprocessor, config = PreprocessorFactory.build(config, method)

        X = df[config.feature_columns]
        y = df[target_column]

        # If the target column contains missing values, drop those rows.
        # Training scikit-learn estimators with NaN in y will raise an error
        # (e.g., "Input y contains NaN"). We drop and record how many rows
        # were removed and log a warning for the user.
        n_missing = int(y.isnull().sum())
        dropped_rows = 0
        if n_missing > 0:
            mask = ~y.isnull()
            X = X.loc[mask].reset_index(drop=True)
            y = y.loc[mask].reset_index(drop=True)
            # Optionally update the stored dataframe to the cleaned version
            df = df.loc[mask].reset_index(drop=True)
            sess["dataframe"] = df
            dropped_rows = n_missing
            app.logger.warning("Dropped %d rows with missing target '%s'", dropped_rows, target_column)

        sess["preprocess_config"] = config
        sess["preprocessor"] = preprocessor
        sess["X"] = X
        sess["y"] = y
        # Persist session after modifications
        _persist_session(session_id, sess)

        summary = {
            "method": config.method,
            "target_column": config.target_column,
            "feature_columns": config.feature_columns,
            "numeric_columns": config.numeric_columns,
            "categorical_columns": config.categorical_columns,
        }

        if dropped_rows:
            summary["dropped_rows_with_missing_target"] = int(dropped_rows)

        return jsonify({"message": "Preprocessing configured.", "summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# 3) Train classification model

@app.route("/api/train", methods=["POST"])
def train_model():
    """
    JSON body:
    {
      "session_id": "...",
      "model_type": "perceptron" | "decision_tree" | "mlp",
      // Optional general param:
      "test_size": 0.3,
      // For MLP:
      "learning_rate": 0.001,
      "hidden_layers": [32, 16],
      "max_iter": 300
    }
    """
    data = request.get_json(force=True)
    try:
        session_id = data["session_id"]
        model_type = data["model_type"].lower()
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400

    test_size = float(data.get("test_size", 0.2))

    try:
        sess = get_session(session_id)

        if sess.get("preprocessor") is None:
            return jsonify({"error": "Preprocessing not configured yet."}), 400

        X = sess["X"]
        y = sess["y"]
        preprocessor = sess["preprocessor"]

        if model_type == "perceptron":
            model = PerceptronModel()
        elif model_type == "decision_tree":
            model = DecisionTreeModel()
        elif model_type in ("mlp", "multilayer_perceptron", "backpropagation"):
            # Accept several ways for users to specify the hidden layers:
            # - hidden_layers: list of ints, e.g. [64, 32]
            # - hidden_layers: comma-separated string, e.g. "64,32"
            # - hidden_layers: single int (one hidden layer)
            # - num_layers + neurons: e.g. num_layers=3, neurons=32 -> (32,32,32)
            def _parse_hidden_layers(value, num_layers_val=None, neurons_val=None):
                # If an explicit hidden_layers value is provided, parse it.
                if value is not None:
                    # list -> convert elements to ints
                    if isinstance(value, list):
                        arr = [int(x) for x in value]
                    # string -> split on commas, semicolons or whitespace
                    elif isinstance(value, str):
                        parts = [p for p in re.split(r"[,;\s]+", value.strip()) if p]
                        if not parts:
                            raise ValueError("hidden_layers string empty")
                        arr = [int(p) for p in parts]
                    # single int
                    elif isinstance(value, int):
                        arr = [int(value)]
                    else:
                        raise ValueError("Unsupported hidden_layers format; use list, CSV string, or int")

                    if any(x <= 0 for x in arr):
                        raise ValueError("All hidden layer sizes must be positive integers")

                    return tuple(arr)

                # Fallback to num_layers + neurons if provided
                if num_layers_val is not None and neurons_val is not None:
                    n_layers = int(num_layers_val)
                    n_neurons = int(neurons_val)
                    if n_layers <= 0 or n_neurons <= 0:
                        raise ValueError("num_layers and neurons must be positive integers")
                    return tuple([n_neurons] * n_layers)

                # Default
                return (100,)

            hidden_input = data.get("hidden_layers")
            # Accept either 'neurons' or commonly misspelled 'nuearals'
            neurons_input = data.get("neurons") or data.get("nuearals")
            num_layers_input = data.get("num_layers")
            try:
                hidden_layers = _parse_hidden_layers(hidden_input, num_layers_input, neurons_input)
            except Exception as e:
                return jsonify({"error": f"Invalid hidden_layers: {e}"}), 400

            learning_rate = float(data.get("learning_rate", 0.001))
            max_iter = int(data.get("max_iter", 300))
            model = MLPBackpropModel(
                hidden_layer_sizes=hidden_layers,
                learning_rate_init=learning_rate,
                max_iter=max_iter,
            )
        else:
            return jsonify({"error": "Unknown model_type"}), 400

        pipeline, result = model.train_and_evaluate(
            X=X, y=y, preprocessor=preprocessor, test_size=test_size
        )

        # store in session so it can be saved later
        sess["models"][model_type] = {"pipeline": pipeline, "metrics": result.to_dict()}
        # Persist updated session
        _persist_session(session_id, sess)

        return jsonify(
            {
                "message": "Model trained successfully.",
                "model_type": model_type,
                "metrics": result.to_dict(),
               # "confusion_matrix": result.cm.tolist(),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 400



@app.route("/api/confusion_matrix", methods=["GET"])
def get_confusion_matrix():
    """Return confusion matrix and metrics for a trained model in a session.

    Query params: ?session_id=...&model_type=perceptron&format=json|html
    """
    session_id = request.args.get("session_id")
    model_type = (request.args.get("model_type") or "").lower()
    fmt = (request.args.get("format") or "json").lower()

    if not session_id or not model_type:
        return jsonify({"error": "Missing session_id or model_type query parameter."}), 400

    try:
        sess = get_session(session_id)
        model_info = sess.get("models", {}).get(model_type)
        if not model_info:
            return jsonify({"error": "No trained model of this type for this session."}), 400

        metrics = model_info.get("metrics", {})

        # If HTML version isn't present, try to build a simple one from the matrix
        cm = metrics.get("confusion_matrix")
        cm_html = metrics.get("confusion_matrix_html")

        def _build_html_from_cm(cm_list):
            if not cm_list:
                return ""
            try:
                n = len(cm_list)
            except Exception:
                return ""
            headers = [f"Pred_{i}" for i in range(n)]
            html = "<table class='confusion-matrix' border='1' cellspacing='0' cellpadding='4'>"
            html += "<thead><tr><th></th>"
            for h in headers:
                html += f"<th>{h}</th>"
            html += "</tr></thead><tbody>"
            for i, row in enumerate(cm_list):
                html += f"<tr><th>Actual_{i}</th>"
                for v in row:
                    html += f"<td>{int(v)}</td>"
                html += "</tr>"
            html += "</tbody></table>"
            return html

        if not cm_html and cm:
            cm_html = _build_html_from_cm(cm)

        # Response includes both JSON matrix and HTML for convenience
        resp = {"model_type": model_type, "metrics": metrics}
        if fmt == "html":
            return jsonify({"confusion_matrix_html": cm_html or ""})
        resp["confusion_matrix"] = cm
        resp["confusion_matrix_html"] = cm_html
        return jsonify(resp)

    except Exception as e:
        return jsonify({"error": str(e)}), 400



# 4) Save model

@app.route("/api/save_model", methods=["POST"])
def save_model():
    """
    JSON body:
    {
      "session_id": "...",
      "model_type": "perceptron" | "decision_tree" | "mlp",
      "model_name": "my_model_1"
    }
    """
    data = request.get_json(force=True)
    try:
        session_id = data["session_id"]
        model_type = data["model_type"].lower()
        model_name = data["model_name"]
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400

    try:
        sess = get_session(session_id)
        model_info = sess["models"].get(model_type)

        if not model_info:
            return jsonify({"error": "No trained model of this type for this session."}), 400

        pipeline = model_info["pipeline"]
        safe_name = "".join(c for c in model_name if c.isalnum() or c in ("_", "-"))
        path = os.path.join("saved_models", f"{safe_name}.joblib")

        dump(pipeline, path)

        return jsonify({"message": "Model saved.", "path": path})
    except Exception as e:
        return jsonify({"error": str(e)}), 400



# 5) Simple health check

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/debug/sessions", methods=["GET"])
def debug_sessions():
    """Return a summary of in-memory sessions for local debugging.

    This endpoint is intentionally gated: it only allows access when the
    Flask app is running with debug=True or when the environment variable
    `ALLOW_DEBUG_SESSIONS=1` is set. Do NOT enable this in production.
    """
    allow = app.debug or os.environ.get("ALLOW_DEBUG_SESSIONS", "0") == "1"
    if not allow:
        return jsonify({"error": "Debug sessions endpoint not allowed."}), 403

    out = {}
    # If Redis is used, fetch keys from Redis; otherwise use in-memory SESSIONS
    if USE_REDIS and redis_client is not None:
        try:
            keys = redis_client.keys("session:*")
            for k in keys:
                sid = k.decode().split(":", 1)[1]
                raw = redis_client.get(k)
                try:
                    sess = pickle.loads(raw) if raw else {}
                except Exception:
                    sess = {}
                df = sess.get("dataframe")
                rows = int(df.shape[0]) if df is not None else 0
                out[sid] = {
                    "rows": rows,
                    "has_preprocessor": bool(sess.get("preprocessor")),
                    "num_models": len(sess.get("models", {})),
                }
        except Exception:
            app.logger.exception("Failed to list sessions from Redis")
    else:
        for sid, sess in SESSIONS.items():
            df = sess.get("dataframe")
            rows = int(df.shape[0]) if df is not None else 0
            out[sid] = {
                "rows": rows,
                "has_preprocessor": bool(sess.get("preprocessor")),
                "num_models": len(sess.get("models", {})),
            }

    return jsonify(out)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port, debug=True)
