/**
 * App.jsx
 * -------
 * Main layout: title, patient form, and prediction results section.
 */
import React, { useState } from "react";
import PatientForm from "./components/PatientForm";
import PredictionResult from "./components/PredictionResult";
import "./App.css";

export default function App() {
  const [predictionData, setPredictionData] = useState(null);
  const [patientPayload, setPatientPayload] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleResult = (data, payload) => {
    setPredictionData(data);
    setPatientPayload(payload);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>ML-Powered Early Disease Prediction System</h1>
        <p>
          Estimate risk of diabetes, cardiovascular disease, and hypertension using
          Logistic Regression, Random Forest, and Neural Network models, with SHAP
          explainability.
        </p>
      </header>

      <main className="app-main">
        <section className="form-section">
          <h2>Patient Information</h2>
          <PatientForm onResult={handleResult} onLoadingChange={setLoading} />
        </section>

        <section className="results-section">
          <h2>Prediction Results</h2>
          {loading && <p>Running predictions...</p>}
          {!loading && !predictionData && <p>Submit the form to see risk predictions.</p>}
          <PredictionResult data={predictionData} patientPayload={patientPayload} />
        </section>
      </main>

      <footer className="app-footer">
        <p>
          <strong>Disclaimer:</strong> This tool is for educational/demonstration purposes
          only and is not a substitute for professional medical advice, diagnosis, or
          treatment.
        </p>
      </footer>
    </div>
  );
}
