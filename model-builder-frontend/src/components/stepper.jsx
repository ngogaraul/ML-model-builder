import "../styles/Stepper.css";

const steps = [
  "Upload",
  "Preprocess",
  "Models",
  "Train",
  "Results"
];

export default function Stepper({ currentStep }) {
  return (
    <div className="stepper">
      {steps.map((label, idx) => {
        const active = idx === currentStep;
        const done = idx < currentStep;

        return (
          <div className="step-item" key={idx}>
            <div className={`step-circle ${done ? "done" : active ? "active" : ""}`}>
              {idx + 1}
            </div>
            <p>{label}</p>
          </div>
        );
      })}
    </div>
  );
}
