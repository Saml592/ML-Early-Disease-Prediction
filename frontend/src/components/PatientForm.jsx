/**
 * PatientForm.jsx
 * ----------------
 * Form collecting all patient fields needed for diabetes, heart disease,
 * and hypertension risk prediction. Performs basic client-side validation,
 * then calls predictDisease() and passes the result up via onResult.
 */
import React, { useState } from "react";
import { predictDisease } from "../services/api";

const initialState = {
  age: "45",
  bmi: "28.4",
  glucose: "130",
  blood_pressure: "80",
  cholesterol: "210",
  family_history: false,
  smoking_status: "Never",
  pregnancies: "2",
  skin_thickness: "25",
  insulin: "85",
  diabetes_pedigree_function: "0.45",
  sex: "1",
  cp: "2",
  fbs: "0",
  restecg: "1",
  thalach: "150",
  exang: "0",
  oldpeak: "1.2",
  slope: "1",
  ca: "0",
  thal: "2",
  sodium_intake: "3200",
  alcohol_units_week: "4",
  physical_activity_min_week: "90",
  stress_score: "6",
  resting_heart_rate: "76"
};

const NUMERIC_FIELDS = new Set([
  "age", "bmi", "glucose", "blood_pressure", "cholesterol",
  "pregnancies", "skin_thickness", "insulin", "diabetes_pedigree_function",
  "sex", "cp", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal",
  "sodium_intake", "alcohol_units_week", "physical_activity_min_week",
  "stress_score", "resting_heart_rate",
]);

export default function PatientForm({ onResult, onLoadingChange }) {
  const [formData, setFormData] = useState(initialState);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState(null);

  const handleChange = (e) => {
    const { name, type, value, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.age) newErrors.age = "Age is required";
    if (formData.age && (formData.age < 1 || formData.age > 120)) {
      newErrors.age = "Age must be between 1 and 120";
    }
    return newErrors;
  };

  const buildPayload = () => {
  const payload = {};
  Object.entries(formData).forEach(([key, value]) => {
    if (key === "family_history") {
      payload[key] = value ? 1 : 0;
    } else if (NUMERIC_FIELDS.has(key)) {
      const num = parseFloat(value);
      // Send null for empty/invalid values instead of 0
      payload[key] = isNaN(num) ? null : num;
    } else {
      payload[key] = value || "";
    }
  });
  return payload;
};

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validate();
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    setSubmitting(true);
    setServerError(null);
    onLoadingChange && onLoadingChange(true);
    try {
      const patientPayload = buildPayload();
      const data = await predictDisease(patientPayload);
      onResult(data, patientPayload);
    } catch (err) {
      const message =
        err?.response?.data?.error || err.message || "Prediction request failed";
      setServerError(message);
    } finally {
      setSubmitting(false);
      onLoadingChange && onLoadingChange(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="patient-form">
      <fieldset>
        <legend>General</legend>
        <label>
          Age*
          <input type="number" name="age" value={formData.age} onChange={handleChange} />
          {errors.age && <span className="field-error">{errors.age}</span>}
        </label>
        <label>
          BMI
          <input type="number" step="0.1" name="bmi" value={formData.bmi} onChange={handleChange} />
        </label>
        <label>
          Glucose (mg/dL)
          <input type="number" name="glucose" value={formData.glucose} onChange={handleChange} />
        </label>
        <label>
          Blood Pressure (mm Hg)
          <input type="number" name="blood_pressure" value={formData.blood_pressure} onChange={handleChange} />
        </label>
        <label>
          Cholesterol (mg/dL)
          <input type="number" name="cholesterol" value={formData.cholesterol} onChange={handleChange} />
        </label>
        <label className="checkbox-label">
          <input type="checkbox" name="family_history" checked={formData.family_history} onChange={handleChange} />
          Family History of Chronic Disease
        </label>
        <label>
          Smoking Status
          <select name="smoking_status" value={formData.smoking_status} onChange={handleChange}>
            <option value="Never">Never</option>
            <option value="Former">Former</option>
            <option value="Current">Current</option>
          </select>
        </label>
      </fieldset>

      <fieldset>
        <legend>Diabetes Indicators</legend>
        <label>
          Pregnancies
          <input type="number" name="pregnancies" value={formData.pregnancies} onChange={handleChange} />
        </label>
        <label>
          Skin Thickness (mm)
          <input type="number" name="skin_thickness" value={formData.skin_thickness} onChange={handleChange} />
        </label>
        <label>
          Insulin (mu U/ml)
          <input type="number" name="insulin" value={formData.insulin} onChange={handleChange} />
        </label>
        <label>
          Diabetes Pedigree Function
          <input
            type="number"
            step="0.01"
            name="diabetes_pedigree_function"
            value={formData.diabetes_pedigree_function}
            onChange={handleChange}
          />
        </label>
      </fieldset>

      <fieldset>
        <legend>Heart Disease Indicators</legend>
        <label>
          Sex
          <select name="sex" value={formData.sex} onChange={handleChange}>
            <option value="1">Male</option>
            <option value="0">Female</option>
          </select>
        </label>
        <label>
          Chest Pain Type
          <select name="cp" value={formData.cp} onChange={handleChange}>
            <option value="0">Typical Angina</option>
            <option value="1">Atypical Angina</option>
            <option value="2">Non-anginal Pain</option>
            <option value="3">Asymptomatic</option>
          </select>
        </label>
        <label>
          Fasting Blood Sugar &gt; 120 mg/dl
          <select name="fbs" value={formData.fbs} onChange={handleChange}>
            <option value="0">No</option>
            <option value="1">Yes</option>
          </select>
        </label>
        <label>
          Resting ECG
          <select name="restecg" value={formData.restecg} onChange={handleChange}>
            <option value="0">Normal</option>
            <option value="1">ST-T Abnormality</option>
            <option value="2">LV Hypertrophy</option>
          </select>
        </label>
        <label>
          Max Heart Rate Achieved
          <input type="number" name="thalach" value={formData.thalach} onChange={handleChange} />
        </label>
        <label>
          Exercise-Induced Angina
          <select name="exang" value={formData.exang} onChange={handleChange}>
            <option value="0">No</option>
            <option value="1">Yes</option>
          </select>
        </label>
        <label>
          ST Depression (oldpeak)
          <input type="number" step="0.1" name="oldpeak" value={formData.oldpeak} onChange={handleChange} />
        </label>
        <label>
          Slope of Peak Exercise ST
          <select name="slope" value={formData.slope} onChange={handleChange}>
            <option value="0">Upsloping</option>
            <option value="1">Flat</option>
            <option value="2">Downsloping</option>
          </select>
        </label>
        <label>
          Major Vessels Colored (0-4)
          <input type="number" min="0" max="4" name="ca" value={formData.ca} onChange={handleChange} />
        </label>
        <label>
          Thalassemia
          <select name="thal" value={formData.thal} onChange={handleChange}>
            <option value="1">Normal</option>
            <option value="2">Fixed Defect</option>
            <option value="3">Reversible Defect</option>
          </select>
        </label>
      </fieldset>

      <fieldset>
        <legend>Hypertension Indicators</legend>
        <label>
          Sodium Intake (mg/day)
          <input type="number" name="sodium_intake" value={formData.sodium_intake} onChange={handleChange} />
        </label>
        <label>
          Alcohol Units / Week
          <input type="number" step="0.1" name="alcohol_units_week" value={formData.alcohol_units_week} onChange={handleChange} />
        </label>
        <label>
          Physical Activity (min/week)
          <input
            type="number"
            name="physical_activity_min_week"
            value={formData.physical_activity_min_week}
            onChange={handleChange}
          />
        </label>
        <label>
          Stress Score (0-10)
          <input type="number" min="0" max="10" name="stress_score" value={formData.stress_score} onChange={handleChange} />
        </label>
        <label>
          Resting Heart Rate (bpm)
          <input type="number" name="resting_heart_rate" value={formData.resting_heart_rate} onChange={handleChange} />
        </label>
      </fieldset>

      {serverError && <div className="server-error">{serverError}</div>}

      <button type="submit" disabled={submitting}>
        {submitting ? "Predicting..." : "Predict Risk"}
      </button>
    </form>
  );
}
