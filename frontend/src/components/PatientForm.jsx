/**
 * PatientForm.jsx
 * ----------------
 * Form collecting all patient fields needed for diabetes, heart disease,
 * and hypertension risk prediction. Lets the user choose which disease(s)
 * to predict, validates only the fields required for those diseases,
 * then calls predictDisease() and passes the result up via onResult.
 */
import React, { useState } from "react";
import { predictDisease } from "../services/api";

// ---------- EMPTY INITIAL STATE (no default values) ----------
const initialState = {
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
  resting_heart_rate: ""
};

const NUMERIC_FIELDS = new Set([
  "age", "bmi", "glucose", "blood_pressure", "cholesterol",
  "pregnancies", "skin_thickness", "insulin", "diabetes_pedigree_function",
  "sex", "cp", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal",
  "sodium_intake", "alcohol_units_week", "physical_activity_min_week",
  "stress_score", "resting_heart_rate",
]);

// Mirrors FEATURE_NAME_MAP keys in backend utils.py — keep these two in sync.
const DISEASE_REQUIRED_FIELDS = {
  diabetes: [
    "pregnancies", "glucose", "blood_pressure", "skin_thickness",
    "insulin", "bmi", "diabetes_pedigree_function", "age",
  ],
  heart: [
    "age", "sex", "cp", "blood_pressure", "cholesterol", "fbs",
    "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal",
  ],
  hypertension: [
    "age", "bmi", "sodium_intake", "smoking_status", "alcohol_units_week",
    "physical_activity_min_week", "family_history", "stress_score",
    "resting_heart_rate", "cholesterol", "glucose",
  ],
};

const DISEASE_LABELS = {
  diabetes: "Diabetes",
  heart: "Cardiovascular Disease",
  hypertension: "Hypertension",
};

// Fields that always have a valid value regardless of what the user touched
// (checkboxes / selects with a default option), so "required" just means
// "make sure the user consciously set it" rather than "is non-empty".
const ALWAYS_VALID_FIELDS = new Set(["family_history", "smoking_status", "sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"]);

export default function PatientForm({ onResult, onLoadingChange }) {
  const [formData, setFormData] = useState(initialState);
  const [selectedDiseases, setSelectedDiseases] = useState(["diabetes", "heart", "hypertension"]);
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

  const toggleDisease = (disease) => {
    setSelectedDiseases((prev) =>
      prev.includes(disease)
        ? prev.filter((d) => d !== disease)
        : [...prev, disease]
    );
  };

  const validate = () => {
    const newErrors = {};

    if (selectedDiseases.length === 0) {
      newErrors._diseases = "Select at least one condition to predict";
      return newErrors;
    }

    if (!formData.age) newErrors.age = "Age is required";
    if (formData.age && (formData.age < 1 || formData.age > 120)) {
      newErrors.age = "Age must be between 1 and 120";
    }

    // Only require fields relevant to the disease(s) actually selected
    const requiredFields = new Set(
      selectedDiseases.flatMap((d) => DISEASE_REQUIRED_FIELDS[d])
    );

    requiredFields.forEach((field) => {
      if (field === "age" || ALWAYS_VALID_FIELDS.has(field)) return; // already valid / handled above
      const val = formData[field];
      if (val === "" || val === null || val === undefined) {
        newErrors[field] = "Required for selected prediction(s)";
      }
    });

    return newErrors;
  };

  const buildPayload = () => {
    const payload = {};
    Object.entries(formData).forEach(([key, value]) => {
      if (key === "family_history") {
        payload[key] = value ? 1 : 0;
      } else if (NUMERIC_FIELDS.has(key)) {
        const num = parseFloat(value);
        if (!isNaN(num)) {
          payload[key] = num; // only include valid numbers
        }
        // if invalid, skip it – don't send null or empty
      } else {
        // For string fields like smoking_status, include if not empty
        if (value && value.trim() !== "") {
          payload[key] = value;
        }
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
      const data = await predictDisease(patientPayload, selectedDiseases);
      onResult(data, patientPayload);
    } catch (err) {
      console.error("Full error response:", err.response?.data);
      const responseData = err?.response?.data;
      const message =
        responseData?.error ||
        (responseData?.errors &&
          Object.entries(responseData.errors)
            .map(([disease, msg]) => `${DISEASE_LABELS[disease] || disease}: ${msg}`)
            .join("; ")) ||
        (responseData?.details &&
          responseData.details
            .map((d) => `${d.loc?.join(".")}: ${d.msg}`)
            .join("; ")) ||
        err.message ||
        "Prediction request failed";
      setServerError(message);
    } finally {
      setSubmitting(false);
      onLoadingChange && onLoadingChange(false);
    }
  };

  // (Optional) Reset the form to empty after successful submission
  // by adding: setFormData(initialState) inside the try block after onResult.

  return (
    <form onSubmit={handleSubmit} className="patient-form">
      <fieldset>
        <legend>Predict For</legend>
        {Object.entries(DISEASE_LABELS).map(([key, label]) => (
          <label key={key} className="checkbox-label">
            <input
              type="checkbox"
              checked={selectedDiseases.includes(key)}
              onChange={() => toggleDisease(key)}
            />
            {label}
          </label>
        ))}
        {errors._diseases && <span className="field-error">{errors._diseases}</span>}
      </fieldset>

      <fieldset>
        <legend>General</legend>
        <label>
          Age*
          <input type="number" name="age" value={formData.age} onChange={handleChange} placeholder="e.g. 45" />
          {errors.age && <span className="field-error">{errors.age}</span>}
        </label>
        <label>
          BMI
          <input type="number" step="0.1" name="bmi" value={formData.bmi} onChange={handleChange} placeholder="e.g. 28.4" />
          {errors.bmi && <span className="field-error">{errors.bmi}</span>}
        </label>
        <label>
          Glucose (mg/dL)
          <input type="number" name="glucose" value={formData.glucose} onChange={handleChange} placeholder="e.g. 130" />
          {errors.glucose && <span className="field-error">{errors.glucose}</span>}
        </label>
        <label>
          Blood Pressure (mm Hg)
          <input type="number" name="blood_pressure" value={formData.blood_pressure} onChange={handleChange} placeholder="e.g. 80" />
          {errors.blood_pressure && <span className="field-error">{errors.blood_pressure}</span>}
        </label>
        <label>
          Cholesterol (mg/dL)
          <input type="number" name="cholesterol" value={formData.cholesterol} onChange={handleChange} placeholder="e.g. 210" />
          {errors.cholesterol && <span className="field-error">{errors.cholesterol}</span>}
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
          <input type="number" name="pregnancies" value={formData.pregnancies} onChange={handleChange} placeholder="e.g. 2" />
          {errors.pregnancies && <span className="field-error">{errors.pregnancies}</span>}
        </label>
        <label>
          Skin Thickness (mm)
          <input type="number" name="skin_thickness" value={formData.skin_thickness} onChange={handleChange} placeholder="e.g. 25" />
          {errors.skin_thickness && <span className="field-error">{errors.skin_thickness}</span>}
        </label>
        <label>
          Insulin (mu U/ml)
          <input type="number" name="insulin" value={formData.insulin} onChange={handleChange} placeholder="e.g. 85" />
          {errors.insulin && <span className="field-error">{errors.insulin}</span>}
        </label>
        <label>
          Diabetes Pedigree Function
          <input
            type="number"
            step="0.01"
            name="diabetes_pedigree_function"
            value={formData.diabetes_pedigree_function}
            onChange={handleChange}
            placeholder="e.g. 0.45"
          />
          {errors.diabetes_pedigree_function && (
            <span className="field-error">{errors.diabetes_pedigree_function}</span>
          )}
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
          <input type="number" name="thalach" value={formData.thalach} onChange={handleChange} placeholder="e.g. 150" />
          {errors.thalach && <span className="field-error">{errors.thalach}</span>}
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
          <input type="number" step="0.1" name="oldpeak" value={formData.oldpeak} onChange={handleChange} placeholder="e.g. 1.2" />
          {errors.oldpeak && <span className="field-error">{errors.oldpeak}</span>}
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
          <input type="number" min="0" max="4" name="ca" value={formData.ca} onChange={handleChange} placeholder="0" />
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
          <input type="number" name="sodium_intake" value={formData.sodium_intake} onChange={handleChange} placeholder="e.g. 3200" />
          {errors.sodium_intake && <span className="field-error">{errors.sodium_intake}</span>}
        </label>
        <label>
          Alcohol Units / Week
          <input type="number" step="0.1" name="alcohol_units_week" value={formData.alcohol_units_week} onChange={handleChange} placeholder="e.g. 4" />
          {errors.alcohol_units_week && <span className="field-error">{errors.alcohol_units_week}</span>}
        </label>
        <label>
          Physical Activity (min/week)
          <input
            type="number"
            name="physical_activity_min_week"
            value={formData.physical_activity_min_week}
            onChange={handleChange}
            placeholder="e.g. 90"
          />
          {errors.physical_activity_min_week && (
            <span className="field-error">{errors.physical_activity_min_week}</span>
          )}
        </label>
        <label>
          Stress Score (0-10)
          <input type="number" min="0" max="10" name="stress_score" value={formData.stress_score} onChange={handleChange} placeholder="e.g. 6" />
          {errors.stress_score && <span className="field-error">{errors.stress_score}</span>}
        </label>
        <label>
          Resting Heart Rate (bpm)
          <input type="number" name="resting_heart_rate" value={formData.resting_heart_rate} onChange={handleChange} placeholder="e.g. 76" />
          {errors.resting_heart_rate && <span className="field-error">{errors.resting_heart_rate}</span>}
        </label>
      </fieldset>

      {serverError && <div className="server-error">{serverError}</div>}

      <button type="submit" disabled={submitting}>
        {submitting ? "Predicting..." : "Predict Risk"}
      </button>
    </form>
  );
}