import { useState, useEffect } from "react";
import { uploadDataset } from "../../api/modelBuilderApi";
import logger from "../../utils/logger";

export default function UploadStep({
  onNext,
  setSession,
  setUploadedData,
  uploadedData,
}) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

  // Local state so UploadStep always rerenders properly
  const [localData, setLocalData] = useState(null);

  // Sync parent → local
  useEffect(() => {
    if (uploadedData) {
      setLocalData(uploadedData);
      logger.debug("SYNCED LOCAL DATA:", uploadedData);
    }
  }, [uploadedData]);

  const handleUpload = async () => {
    if (!file) {
      alert("Select a file first.");
      return;
    }

    setLoading(true);

    try {
      const res = await uploadDataset(file);

      logger.debug("BACKEND RESPONSE (raw):", res);

      // If backend returned invalid JSON (e.g. bare NaN), axios may
      // expose the raw response as a string. Try to coerce to an object
      // by replacing bare NaN with null and parsing.
      let data = res;
      if (typeof res === "string") {
        try {
          const cleaned = res.replace(/\bNaN\b/g, "null");
          data = JSON.parse(cleaned);
          logger.debug("Parsed backend string response to object.", data);
        } catch (parseErr) {
          console.warn("⚠ Could not parse backend response string; keeping raw value.", parseErr);
          data = res;
        }
      }

      setSession(data?.session_id);
      setUploadedData(data);
      setLocalData(data); // for immediate preview

    } catch (err) {
      alert("Upload error: " + (err.response?.data?.error || err.message));
    }

    setLoading(false);
  };

  const columns = Array.isArray(localData?.columns) ? localData.columns : [];
  const preview = Array.isArray(localData?.preview) ? localData.preview : [];

  return (
    <div className="form-card">
      <h2>Upload Dataset</h2>

      <input
        type="file"
        accept=".csv,.xlsx"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? "Uploading..." : localData ? "Re-upload" : "Upload"}
      </button>

      <h3 style={{ marginTop: "20px" }}>Dataset Preview</h3>

      {!localData && (
        <p style={{ color: "gray" }}>Upload a dataset to see preview.</p>
      )}

      {localData && (
        <>
          <p>
            Rows: <strong>{localData.num_rows}</strong> | Columns:{" "}
            <strong>{localData.num_cols}</strong>
          </p>

          <div
            style={{
              overflowX: "auto",
              padding: "10px",
              background: "white",
              border: "1px solid #ccc",
            }}
          >
            <table border="1" cellPadding="6" style={{ width: "100%" }}>
              <thead>
                <tr>
                  {columns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.map((row, i) => (
                  <tr key={i}>
                    {columns.map((col) => (
                      <td key={col}>{String(row[col])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <button style={{ marginTop: "20px" }} onClick={onNext}>
            Next → Preprocessing
          </button>
        </>
      )}
    </div>
  );
}
