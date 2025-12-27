import { useState, useMemo } from "react";
import { preprocessData } from "../../api/modelBuilderApi";
import logger from "../../utils/logger";

export default function PreprocessStep({
  session,
  uploadedData,
  onNext,
  onBack,
  setPreprocessSummary,
}) {
  const [method, setMethod] = useState(null);
  const [target, setTarget] = useState("");

  // ❗ Guard if no dataset was uploaded
  if (!uploadedData) {
    return (
      <div>
        <h2>Error</h2>
        <p>No dataset loaded. Please go back and upload a dataset.</p>
        <button onClick={onBack}>← Back</button>
      </div>
    );
  }

  // ✅ FIX: Build columns list safely using fallback strategy
  const columns = useMemo(() => {
    logger.debug("Extracting columns...");

    if (uploadedData?.columns && uploadedData.columns.length > 0) {
      logger.debug("Using backend-provided columns:", uploadedData.columns);
      return uploadedData.columns;
    }

    if (uploadedData?.preview && uploadedData.preview.length > 0) {
      const inferred = Object.keys(uploadedData.preview[0]);
      logger.debug("Inferred columns from preview:", inferred);
      return inferred;
    }

    console.warn("⚠ No columns found. Returning empty array.");
    return [];
  }, [uploadedData]);

  logger.debug("PREPROCESS final columns:", columns);

  const handlePreprocess = async () => {
    if (!target) return alert("Please select target column.");
    if (!method) return alert("Please select a preprocessing method.");

    try {
      const payload = {
        session_id: session,
        method: method,
        target_column: target,
      };

      const response = await preprocessData(payload);

      logger.debug("Preprocess Response:", response);

      setPreprocessSummary(response.summary);
      onNext();
    } catch (err) {
      alert("Preprocess error: " + (err.response?.data?.error || err.message));
    }
  };

  return (
    <div className="form-card">
      <h2>Preprocessing</h2>

      {/* Target Column Selector */}
      <h3>Select Target Column</h3>

      <select
        value={target}
        onChange={(e) => setTarget(e.target.value)}
        style={{ width: "240px", padding: "6px" }}
      >
        <option value="">-- Choose column --</option>

        {columns.map((col) => (
          <option key={col} value={col}>
            {col}
          </option>
        ))}
      </select>

      <p style={{ color: "gray" }}>Debug → Columns count: {columns.length}</p>

      {columns.length === 0 && (
        <div
          style={{
            marginTop: 12,
            background: "#f9f9f9",
            padding: 10,
            border: "1px solid #eee",
            maxWidth: 700,
          }}
        >
          <strong>Debug — Raw uploadedData</strong>
          <pre style={{ maxHeight: 220, overflow: "auto", marginTop: 8 }}>
            {JSON.stringify(uploadedData, null, 2)}
          </pre>
        </div>
      )}

      {/* Method Selection */}
      <h3 style={{ marginTop: "20px" }}>Preprocessing Method</h3>

      <label>
        <input
          type="radio"
          value="normalization"
          checked={method === "normalization"}
          onChange={(e) => setMethod(e.target.value)}
        />
        Normalization
      </label>
      <br />

      <label>
        <input
          type="radio"
          value="onehot"
          checked={method === "onehot"}
          onChange={(e) => setMethod(e.target.value)}
        />
        One-Hot Encoding
      </label>

      {/* Buttons */}
      <div style={{ marginTop: "30px" }}>
        <button onClick={onBack} style={{ marginRight: "20px" }}>
          ← Back
        </button>
        <button onClick={handlePreprocess}>Next → Choose Model</button>
      </div>
    </div>
  );
}
