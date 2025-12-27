import { useState } from "react";

export default function ModelSelectStep({
  onNext,
  onBack,
  setSelectedModels,
}) {
  const [models, setModels] = useState({
    perceptron: false,
    decision_tree: false,
    mlp: false,
  });

  const handleNext = () => {
    const selected = Object.keys(models).filter((m) => models[m]);
    if (selected.length === 0)
      return alert("Select at least one model.");

    setSelectedModels(selected);
    onNext();
  };

  return (
    <div className="form-card">
      <h2>Select Models</h2>

      {Object.keys(models).map((m) => (
        <label key={m}>
          <input
            type="checkbox"
            checked={models[m]}
            onChange={() =>
              setModels({ ...models, [m]: !models[m] })
            }
          />
          {m}
        </label>
      ))}

      <div className="buttons">
        <button onClick={onBack}>← Back</button>
        <button onClick={handleNext}>Next →</button>
      </div>
    </div>
  );
}
