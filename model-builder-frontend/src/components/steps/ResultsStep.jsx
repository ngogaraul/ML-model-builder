import { useState, useEffect } from "react";
import { saveModel, getConfusionMatrix } from "../../api/modelBuilderApi";

export default function ResultsStep({ onBack, results, session }) {
  const formatNumber = (v) => {
    if (v === null || v === undefined) return "";
    if (typeof v === "number" && Number.isFinite(v)) return v.toFixed(3);
    const n = Number(v);
    if (!Number.isNaN(n) && isFinite(n)) return n.toFixed(3);
    return String(v);
  };
  const [modelNames, setModelNames] = useState({}); // model_type → input name
  const [saving, setSaving] = useState({});         // model_type → loading state
  const [confusionMatrices, setConfusionMatrices] = useState({}); // model_type → { confusion_matrix, confusion_matrix_html }
  const [cmLoading, setCmLoading] = useState({});
  const [cmError, setCmError] = useState({});

  const handleSave = async (modelType) => {
    const name = modelNames[modelType];

    if (!name) {
      alert("Please enter a model name.");
      return;
    }

    setSaving({ ...saving, [modelType]: true });

    try {
      const res = await saveModel({
        session_id: session,
        model_type: modelType,
        model_name: name,
      });

      alert(`Model saved successfully!\nLocation: ${res.path}`);
    } catch (err) {
      alert("Error saving model: " + (err.response?.data?.error || err.message));
    }

    setSaving({ ...saving, [modelType]: false });
  };

  useEffect(() => {
    if (!session || !results) return;

    const modelTypes = Object.keys(results || {});

    modelTypes.forEach(async (mt) => {
      setCmLoading((s) => ({ ...s, [mt]: true }));
      setCmError((s) => ({ ...s, [mt]: null }));
      try {
        const data = await getConfusionMatrix({ session_id: session, model_type: mt });
        // API returns either {confusion_matrix, confusion_matrix_html} or error
        setConfusionMatrices((s) => ({ ...s, [mt]: data }));
      } catch (err) {
        setCmError((s) => ({ ...s, [mt]: err.response?.data?.error || err.message }));
      } finally {
        setCmLoading((s) => ({ ...s, [mt]: false }));
      }
    });
  }, [session, results]);

  return (
    <div className="form-card">
      <h2>Training Results</h2>

      {Object.entries(results).map(([modelType, metrics]) => (
        <div key={modelType} style={{ marginBottom: "25px" }}>
          <h3>{modelType.toUpperCase()}</h3>

          {/* Metrics (skip confusion matrix entries, shown below) */}
          {Object.entries(metrics)
            .filter(([k]) => k !== "confusion_matrix" && k !== "confusion_matrix_html")
            .map(([k, v]) => (
              <p key={k}>
                <strong>{k}: </strong> {formatNumber(v)}
              </p>
            ))}

          {/* Confusion matrix */}
          <div style={{ marginTop: "10px" }}>
            {cmLoading[modelType] && <p>Loading confusion matrix...</p>}
            {cmError[modelType] && <p style={{ color: "red" }}>{cmError[modelType]}</p>}
            {confusionMatrices[modelType] && confusionMatrices[modelType].confusion_matrix && (
              (() => {
                const cm = confusionMatrices[modelType].confusion_matrix;
                const n = cm.length || 0;
                return (
                  <table className="confusion-matrix" border="1" cellSpacing="0" cellPadding="6">
                    <thead>
                      <tr>
                        <th></th>
                        {Array.from({ length: n }).map((_, i) => (
                          <th key={i}>Pred_{i}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {cm.map((row, i) => (
                        <tr key={i}>
                          <th>Actual_{i}</th>
                          {row.map((v, j) => (
                            <td key={j}>{formatNumber(v)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                );
              })()
            )}
            {confusionMatrices[modelType] && !confusionMatrices[modelType].confusion_matrix && confusionMatrices[modelType].confusion_matrix_html && (
              <div dangerouslySetInnerHTML={{ __html: confusionMatrices[modelType].confusion_matrix_html }} />
            )}
          </div>

          {/* Save model form */}
          <div style={{ marginTop: "10px" }}>
            <label>Model Name</label>
            <input
              type="text"
              placeholder="my_model_name"
              value={modelNames[modelType] || ""}
              onChange={(e) =>
                setModelNames({
                  ...modelNames,
                  [modelType]: e.target.value,
                })
              }
            />
          </div>

          <button
            style={{ marginTop: "10px" }}
            onClick={() => handleSave(modelType)}
            disabled={saving[modelType]}
          >
            {saving[modelType] ? "Saving..." : `Save ${modelType} Model`}
          </button>
        </div>
      ))}

      <button onClick={onBack}>← Back</button>
    </div>
  );
}
