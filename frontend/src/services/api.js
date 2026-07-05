/**
 * api.js
 * ------
 * Axios instance configured for the Flask backend, plus wrapper functions
 * for /predict, /explain, and /report endpoints.
 */
import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:5000";

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 60000,   // 60 s — PDF generation can take ~10-20 s
});

/**
 * Run risk prediction for one or more diseases.
 * @param {object} patient  – PatientData fields
 * @param {string[]} [diseases] – optional subset
 * @returns {Promise<object>} { results, errors? }
 */
export async function predictDisease(patient, diseases = undefined) {
  const body = diseases ? { patient, diseases } : { patient };
  const response = await apiClient.post("/predict", body);
  return response.data;
}

/**
 * Get SHAP explanation for a single disease prediction.
 * @param {string} disease     – "diabetes" | "heart" | "hypertension"
 * @param {object} patient     – PatientData fields
 * @param {string} [modelType] – "random_forest" (default) | "logistic_regression" | "ann"
 * @returns {Promise<object>}
 */
export async function explainDisease(disease, patient, modelType = "random_forest") {
  const response = await apiClient.post(`/explain/${disease}`, {
    patient,
    model_type: modelType,
  });
  return response.data;
}

/**
 * Request a PDF risk report from the server.
 *
 * The backend renders a Jinja2 template with SHAP charts and converts it to
 * PDF via WeasyPrint.  If WeasyPrint is not available on the server the
 * response is an HTML file instead (same filename convention, .html suffix).
 *
 * @param {object} patient      – PatientData fields (same as /predict)
 * @param {object} predictions  – pre-computed /predict response body
 * @param {string} [modelType]  – SHAP model type (default "random_forest")
 * @param {string[]} [diseases] – optional subset of diseases to include
 * @returns {Promise<{blob: Blob, filename: string}>}
 */
export async function downloadReport(
  patient,
  predictions = undefined,
  modelType = "random_forest",
  diseases = undefined
) {
  const body = { patient, model_type: modelType };
  if (predictions) body.predictions = predictions;
  if (diseases)    body.diseases    = diseases;

  const response = await apiClient.post("/report", body, {
    responseType: "blob",
    timeout: 90000,   // PDF generation can be slow on first call (model load)
  });

  // Derive filename from Content-Disposition header, fallback to timestamp
  const disposition = response.headers["content-disposition"] || "";
  const nameMatch   = disposition.match(/filename="?([^";\n]+)"?/i);
  const contentType = response.headers["content-type"] || "";
  const ext         = contentType.includes("pdf") ? "pdf" : "html";
  const filename    = nameMatch
    ? nameMatch[1]
    : `disease_risk_report_${Date.now()}.${ext}`;

  return { blob: response.data, filename };
}

export default apiClient;
