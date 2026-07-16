/**
 * ExplainableAI.jsx
 * -----------------
 * Page for SHAP-based explainability of disease predictions.
 * Users select a disease, fill in patient data, and view SHAP feature importance.
 */

import React, { useState } from "react";
import { explainDisease } from "../services/api";
import ShapChart from "../components/ShapChart";
import "../styles/ExplainableAI.css";

const DISEASE_OPTIONS = [
  { value: "diabetes", label: "Diabetes" },
  { value: "heart", label: "Cardiovascular Disease" },
  { value: "hypertension", label: "Hypertension" },
];

const MODEL_OPTIONS = [
  { value: "logistic_regression", label: "Logistic Regression" },
  { value: "random_forest", label: "Random Forest" },
  { value: "ann", label: "Neural Network (ANN)" },
];

// Default patient data (empty)
const EMPTY_PATIENT = {
  age: "",
  bmi: "",
  glucose: "",
  blood_pressure: "",
  cholesterol: "",
  family_history: false,
  smoking_status: "Never",
  pregnancies: "",
  skin_thickness: "",
  insulin: "",
  diabetes_pedigree_function: "",
  sex: "1",
  cp: "2",
  fbs: "0",
  restecg: "1",
  thalach: "",
  exang: "0",
  oldpeak: "",
  slope: "1",
  ca: "0",
  thal: "2",
  sodium_intake: "",
  alcohol_units_week: "",
  physical_activity_min_week: "",
  stress_score: "",
  resting_heart_rate: "",
};

const NUMERIC_FIELDS = new Set([
  "age", "bmi", "glucose", "blood_pressure", "cholesterol",
  "pregnancies", "skin_thickness", "insulin", "diabetes_pedigree_function",
  "sex", "cp", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal",
  "sodium_intake", "alcohol_units_week", "physical_activity_min_week",
  "stress_score", "resting_heart_rate",
]);

export default function ExplainableAI() {
  const [disease, setDisease] = useState("diabetes");
  const [modelType, setModelType] = useState("random_forest");
  const [patient, setPatient] = useState(EMPTY_PATIENT);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePatientChange = (e) => {
    const { name, type, value, checked } = e.target;
    setPatient((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const buildPayload = () => {
    const payload = {};
    Object.entries(patient).forEach(([key, value]) => {
      if (key === "family_history") {
        payload[key] = value ? 1 : 0;
      } else if (NUMERIC_FIELDS.has(key)) {
        const num = parseFloat(value);
        payload[key] = isNaN(num) ? null : num;
      } else {
        payload[key] = value || "";
      }
    });
    return payload;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setExplanation(null);

    try {
      const payload = buildPayload();
      const result = await explainDisease(disease, payload, modelType);
      setExplanation(result);
    } catch (err) {
      const msg = err?.response?.data?.error || err.message || "Explanation failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPatient(EMPTY_PATIENT);
    setExplanation(null);
    setError(null);
  };

  // Helper to render form fields (reuse layout from PatientForm)
  // We'll keep it simple here; you can expand if needed.
  const renderField = (name, label, type = "text", step = null) => (
    <label key={name}>
      {label}
      <input
        type={type}
        name={name}
        value={patient[name] ?? ""}
        onChange={handlePatientChange}
        step={step}
      />
    </label>
  );

  return (
    <div className="explainable-ai-page">
      <div className="page-header">
        <h1>Explainable AI (SHAP)</h1>
        <p>Understand model predictions with SHAP explanations</p>
      </div>

      <div className="explainable-layout">
        <div className="explainable-form">
          <form onSubmit={handleSubmit}>
            <fieldset>
              <legend>Disease & Model</legend>
              <label>
                Disease
                <select value={disease} onChange={(e) => setDisease(e.target.value)}>
                  {DISEASE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </label>
              <label>
                Model
                <select value={modelType} onChange={(e) => setModelType(e.target.value)}>
                  {MODEL_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </label>
            </fieldset>

            <fieldset>
              <legend>Patient Data</legend>
              {renderField("age", "Age *", "number")}
              {renderField("bmi", "BMI", "number", "0.1")}
              {renderField("glucose", "Glucose (mg/dL)", "number")}
              {renderField("blood_pressure", "Blood Pressure (mm Hg)", "number")}
              {renderField("cholesterol", "Cholesterol (mg/dL)", "number")}
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="family_history"
                  checked={patient.family_history}
                  onChange={handlePatientChange}
                />
                Family History of Chronic Disease
              </label>
              <label>
                Smoking Status
                <select name="smoking_status" value={patient.smoking_status} onChange={handlePatientChange}>
                  <option value="Never">Never</option>
                  <option value="Former">Former</option>
                  <option value="Current">Current</option>
                </select>
              </label>
              {/* Add more fields as needed; for brevity, I'm including key ones */}
              {renderField("pregnancies", "Pregnancies", "number")}
              {renderField("skin_thickness", "Skin Thickness (mm)", "number")}
              {renderField("insulin", "Insulin (mu U/ml)", "number")}
              {renderField("diabetes_pedigree_function", "Diabetes Pedigree", "number", "0.01")}
              {renderField("thalach", "Max Heart Rate", "number")}
              {renderField("oldpeak", "ST Depression (oldpeak)", "number", "0.1")}
              {renderField("sodium_intake", "Sodium Intake (mg/day)", "number")}
              {renderField("alcohol_units_week", "Alcohol Units / Week", "number", "0.1")}
              {renderField("physical_activity_min_week", "Physical Activity (min/week)", "number")}
              {renderField("stress_score", "Stress Score (0-10)", "number")}
              {renderField("resting_heart_rate", "Resting Heart Rate (bpm)", "number")}
            </fieldset>

            <div className="form-actions">
              <button type="submit" disabled={loading}>
                {loading ? "Explaining..." : "Explain Prediction"}
              </button>
              <button type="button" onClick={handleReset}>
                Reset
              </button>
            </div>
          </form>
        </div>

        <div className="explainable-results">
          {error && <div className="error-message">{error}</div>}
          {explanation && (
            <div className="explanation-container">
              <h3>SHAP Explanation for {disease}</h3>
              <p>
                Model: {modelType} &nbsp;|&nbsp; Base value: {explanation.base_value?.toFixed(4)} &nbsp;|&nbsp; Predicted: {explanation.predicted_probability?.toFixed(4)}
              </p>
              <ShapChart
                disease={disease}
                modelType={modelType}
                patientPayload={patient}
                explanation={explanation}  // if ShapChart expects it
              />
              {/* If ShapChart doesn't accept explanation prop, we might need to adapt */}
              <div className="feature-table">
                <h4>Feature Contributions</h4>
                <table>
                  <thead>
                    <tr>
                      <th>Feature</th>
                      <th>SHAP Value</th>
                      <th>Contribution %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(explanation.feature_contributions || {}).map(([feat, data]) => (
                      <tr key={feat}>
                        <td>{feat}</td>
                        <td>{data.shap_value?.toFixed(4)}</td>
                        <td>{data.contribution_pct?.toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
