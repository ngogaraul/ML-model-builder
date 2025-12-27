import { useState } from "react";
import logger from "../utils/logger";

import Stepper from "../components/stepper";

import UploadStep from "../components/steps/UploadStep";
import PreprocessStep from "../components/steps/PreprocessStep";
import ModelSelectStep from "../components/steps/ModelSelectStep";
import TrainStep from "../components/steps/TrainStep";
import ResultsStep from "../components/steps/ResultsStep";

export default function ModelBuilder() {
  const [currentStep, setCurrentStep] = useState(0);

  const [session, setSession] = useState(null);
  const [uploadedData, setUploadedData] = useState(null);
  const [preprocessSummary, setPreprocessSummary] = useState(null);
  const [selectedModels, setSelectedModels] = useState([]);
  const [results, setResults] = useState(null);

  logger.debug("MODELBUILDER uploadedData:", uploadedData);

  const goNext = () => setCurrentStep((s) => s + 1);
  const goBack = () => setCurrentStep((s) => s - 1);

  return (
    <div className="wizard-container">

      <Stepper currentStep={currentStep} />

      {currentStep === 0 && (
        <UploadStep
          onNext={goNext}
          setSession={setSession}
          setUploadedData={setUploadedData}
          uploadedData={uploadedData}   // <-- IMPORTANT
        />
      )}

      {currentStep === 1 && (
        <PreprocessStep
          onNext={goNext}
          onBack={goBack}
          session={session}
          uploadedData={uploadedData}
          setPreprocessSummary={setPreprocessSummary}
        />
      )}

      {currentStep === 2 && (
        <ModelSelectStep
          onNext={goNext}
          onBack={goBack}
          setSelectedModels={setSelectedModels}
        />
      )}

      {currentStep === 3 && (
        <TrainStep
          onNext={goNext}
          onBack={goBack}
          session={session}
          selectedModels={selectedModels}
          setResults={setResults}
        />
      )}

      {currentStep === 4 && (
        <ResultsStep
          onBack={goBack}
          session={session}
          results={results}
        />
      )}

    </div>
  );
}
