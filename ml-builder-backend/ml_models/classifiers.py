
from dataclasses import dataclass, asdict
from typing import Any, Dict, Tuple

import pandas as pd
from sklearn.linear_model import Perceptron
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from sklearn.compose import ColumnTransformer


@dataclass
class TrainResult:
    model_type: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    confusion_matrix: Any
    test_size: float

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Confusion matrix as nested lists (JSON-serializable)
        try:
            cm_list = self.confusion_matrix.tolist()
        except Exception:
            # If it's already a list or other, fallback
            cm_list = self.confusion_matrix

        d["confusion_matrix"] = cm_list

        # Also provide a simple HTML table representation useful for quick frontend
        # rendering. Rows are actual, columns are predicted. Use numeric labels
        # 0..n-1 when class labels aren't available.
        try:
            n = len(cm_list)
        except Exception:
            n = 0

        headers = [f"Pred_{i}" for i in range(n)]
        rows = []
        for i in range(n):
            row_vals = cm_list[i] if i < len(cm_list) else []
            rows.append(row_vals)

        # build HTML table
        html = "<table class='confusion-matrix' border='1' cellspacing='0' cellpadding='4'>"
        # header
        html += "<thead><tr><th></th>"
        for h in headers:
            html += f"<th>{h}</th>"
        html += "</tr></thead>"
        # body
        html += "<tbody>"
        for i, row in enumerate(rows):
            html += f"<tr><th>Actual_{i}</th>"
            for v in row:
                html += f"<td>{int(v)}</td>"
            html += "</tr>"
        html += "</tbody></table>"

        d["confusion_matrix_html"] = html
        return d


class BaseClassifierModel:
    def __init__(self, model_type: str):
        self.model_type = model_type
        self.pipeline: Pipeline | None = None

    def _build_pipeline(self, preprocessor: ColumnTransformer, estimator) -> Pipeline:
        return Pipeline(steps=[("preprocess", preprocessor), ("clf", estimator)])

    def train_and_evaluate(
        self,
        X: pd.DataFrame,
        y,
        preprocessor: ColumnTransformer,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Tuple[Pipeline, TrainResult]:

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        self.pipeline = self._build_pipeline(preprocessor, self._build_estimator())

        self.pipeline.fit(X_train, y_train)
        y_pred = self.pipeline.predict(X_test)

        # Use macro-averaging for precision/recall/f1 so they reflect per-class
        # performance instead of matching accuracy (weighted recall equals
        # overall accuracy because it's a support-weighted average of recalls).
        result = TrainResult(
            model_type=self.model_type,
            accuracy=accuracy_score(y_test, y_pred),
            precision=precision_score(y_test, y_pred, average="macro", zero_division=0),
            recall=recall_score(y_test, y_pred, average="macro", zero_division=0),
            f1=f1_score(y_test, y_pred, average="macro", zero_division=0),
            confusion_matrix=confusion_matrix(y_test, y_pred),
            test_size=test_size,
        )
        return self.pipeline, result
    def _build_estimator(self):
        """Implemented in subclasses."""
        raise NotImplementedError


class PerceptronModel(BaseClassifierModel):
    def __init__(self, **kwargs):
        super().__init__("perceptron")
        self.kwargs = kwargs

    def _build_estimator(self):
        return Perceptron(**self.kwargs)


class DecisionTreeModel(BaseClassifierModel):
    def __init__(self, **kwargs):
        super().__init__("decision_tree")
        self.kwargs = kwargs

    def _build_estimator(self):
        # sensible defaults; can be overridden via kwargs
        default = dict(max_depth=None, random_state=42)
        default.update(self.kwargs)
        return DecisionTreeClassifier(**default)


class MLPBackpropModel(BaseClassifierModel):
    def __init__(self, hidden_layer_sizes=(100,), learning_rate_init=0.001, max_iter=300, **kwargs):
        super().__init__("multilayer_perceptron")
        self.hidden_layer_sizes = hidden_layer_sizes
        self.learning_rate_init = learning_rate_init
        self.max_iter = max_iter
        self.kwargs = kwargs

    def _build_estimator(self):
        # Ensure max_iter is an integer and provide sensible termination defaults
        try:
            max_iter_val = int(self.max_iter)
        except Exception:
            max_iter_val = 300

        params = dict(
            hidden_layer_sizes=self.hidden_layer_sizes,
            learning_rate_init=self.learning_rate_init,
            max_iter=max_iter_val,
            random_state=42,
        )
        # Provide safe defaults which help ensure the estimator will terminate
        # promptly unless the caller explicitly overrides them via kwargs.
        if "tol" not in self.kwargs:
            params["tol"] = 1e-4
        if "n_iter_no_change" not in self.kwargs:
            params["n_iter_no_change"] = 10
        if "early_stopping" not in self.kwargs:
            params["early_stopping"] = False
        if "verbose" not in self.kwargs:
            params["verbose"] = False
        params.update(self.kwargs)
        return MLPClassifier(**params)
