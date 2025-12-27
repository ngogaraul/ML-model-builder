import { useState } from "react";
import { trainModel } from "../../api/modelBuilderApi";

export default function TrainStep({
  onNext,
  onBack,
  session,
  selectedModels,
  setResults,
}) {
  const [trainSize, setTrainSize] = useState(80);
  const [loading, setLoading] = useState(false);
  // MLP-specific parameters (applied only when training 'mlp')
  const [hiddenLayers, setHiddenLayers] = useState("");
  const [neurons, setNeurons] = useState(32);
  const [numLayers, setNumLayers] = useState(1);
  const [learningRate, setLearningRate] = useState(0.001);
  const [maxIter, setMaxIter] = useState(300);

  const handleTrain = async () => {
    setLoading(true);
    const output = {};

    for (const m of selectedModels) {
      try {
        // Build base payload
        const payload = {
          session_id: session,
          model_type: m,
          test_size: 1 - trainSize / 100,
        };

        // If model is MLP, attach optional hyperparameters
        if (m === "mlp" || m === "multilayer_perceptron" || m === "backpropagation") {
          if (hiddenLayers) payload.hidden_layers = hiddenLayers;
          if (neurons) payload.neurons = Number(neurons);
          if (numLayers) payload.num_layers = Number(numLayers);
          if (learningRate) payload.learning_rate = Number(learningRate);
          if (maxIter) payload.max_iter = Number(maxIter);
        }

        const res = await trainModel(payload);

        output[m] = res.metrics;
      } catch (err) {
        alert(m + " error: " + err.response?.data?.error);
      }
    }

    setResults(output);
    setLoading(false);
    onNext();
  };

  return (
    <div className="form-card">
      <h2>Train Models</h2>

      <label>Training %</label>
      <input
        type="number"
        value={trainSize}
        onChange={(e) => setTrainSize(e.target.value)}
      />

      {/* Show MLP options only if MLP is selected */}
      {selectedModels.includes("mlp") && (
        <div style={{ marginTop: 16, padding: 12, border: "1px dashed #ddd" }}>
          <h3>MLP Options</h3>

          <label>Hidden layers (CSV or single int)</label>
          <input
            type="text"
            placeholder="e.g. 64,32 or 128"
            value={hiddenLayers}
            onChange={(e) => setHiddenLayers(e.target.value)}
            style={{ width: 260 }}
          />
          <div style={{ color: "#666", marginBottom: 8 }}>
            Or set <strong>num_layers</strong> and <strong>neurons</strong>.
          </div>
          {/*
          <label>Neurons (per layer)</label>
          <input
            type="number"
            value={neurons}
            onChange={(e) => setNeurons(e.target.value)}
            style={{ width: 120 }}
          />

          <label style={{ marginLeft: 12 }}>Num layers</label>
          <input
            type="number"
            value={numLayers}
            onChange={(e) => setNumLayers(e.target.value)}
            style={{ width: 80 }}
          />*/}

          <div style={{ marginTop: 10 }}>
            <label>Learning rate</label>
            <input
              type="number"
              step="0.0001"
              value={learningRate}
              onChange={(e) => setLearningRate(e.target.value)}
              style={{ width: 120 }}
            />

            <label style={{ marginLeft: 12 }}>Max iterations</label>
            <input
              type="number"
              value={maxIter}
              onChange={(e) => setMaxIter(e.target.value)}
              style={{ width: 120 }}
            />
          </div>
        </div>
      )}

      <div className="buttons">
        <button onClick={onBack}>← Back</button>
        <button onClick={handleTrain} disabled={loading}>
          {loading ? "Training..." : "Start Training →"}
        </button>
      </div>
    </div>
  );
}
