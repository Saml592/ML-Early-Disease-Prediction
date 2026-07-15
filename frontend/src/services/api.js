/**
 * api.js
 * ------
 * Axios instance using the React proxy (no CORS in dev).
 * All requests are relative; the proxy forwards to http://localhost:5000.
 * Includes JWT interceptor and 401 handling.
 */

import axios from "axios";


const baseURL = process.env.REACT_APP_API_BASE_URL || process.env.REACT_APP_API_URL || "";
console.log("🔍 API Base URL:", baseURL);
const apiClient = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
  timeout: 90000,
});
// ---- Request interceptor: attach JWT token ----
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("authToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ---- Response interceptor: handle 401 ----
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("authToken");
      localStorage.removeItem("user");
      if (!window.location.pathname.includes("/signin")) {
        window.location.href = "/signin";
      }
    }
    return Promise.reject(error);
  }
);

// ============================================================
//  AUTH
// ============================================================
export const login = (username, password) =>
  apiClient.post("/auth/login", { username, password });

export const register = (username, email, password) =>
  apiClient.post("/auth/register", { username, email, password });

// ============================================================
//  PREDICT
// ============================================================
export const predictDisease = (patient, diseases) => {
  const body = diseases ? { patient, diseases } : { patient };
  return apiClient.post("/predict", body).then(res => res.data);
};

// ============================================================
//  EXPLAIN (SHAP)
// ============================================================
export const explainDisease = (disease, patient, modelType = "random_forest") =>
  apiClient.post(`/explain/${disease}`, { patient, model_type: modelType })
    .then(res => res.data);

// ============================================================
//  REPORT
// ============================================================
export const downloadReport = async (patient, predictions, modelType = "random_forest", diseases) => {
  const body = { patient, model_type: modelType };
  if (predictions) body.predictions = predictions;
  if (diseases) body.diseases = diseases;

  const response = await apiClient.post("/api/reports/report", body, {
    responseType: "blob",
    timeout: 90000,
  });

  const disposition = response.headers["content-disposition"] || "";
  const nameMatch = disposition.match(/filename="?([^";\n]+)"?/i);
  const contentType = response.headers["content-type"] || "";
  const ext = contentType.includes("pdf") ? "pdf" : "html";
  const filename = nameMatch ? nameMatch[1] : `disease_risk_report_${Date.now()}.${ext}`;

  return { blob: response.data, filename };
};

// ============================================================
//  DASHBOARD
// ============================================================
export const getDashboardMetrics = () =>
  apiClient.get("/api/dashboard/metrics").then(res => res.data);

export const getDailyPredictions = () =>
  apiClient.get("/api/dashboard/daily-predictions").then(res => res.data);

export const getDiseaseDistribution = () =>
  apiClient.get("/api/dashboard/disease-distribution").then(res => res.data);

export const getRiskDistribution = () =>
  apiClient.get("/api/dashboard/risk-distribution").then(res => res.data);

export const getMonthlyAccuracy = () =>
  apiClient.get("/api/dashboard/monthly-accuracy").then(res => res.data);

export const getRecentPredictions = (limit = 10, offset = 0) =>
  apiClient.get(`/api/dashboard/recent-predictions?limit=${limit}&offset=${offset}`)
    .then(res => res.data);

// ============================================================
//  ANALYTICS
// ============================================================
export const getAnalyticsSummary = () =>
  apiClient.get("/api/analytics/summary").then(res => res.data);

export const getPredictionsByDate = (days = 30) =>
  apiClient.get(`/api/analytics/predictions-by-date?days=${days}`).then(res => res.data);

export const getModelPerformance = () =>
  apiClient.get("/api/analytics/model-performance").then(res => res.data);

export const getAnalyticsRiskDistribution = () =>
  apiClient.get("/api/analytics/risk-distribution").then(res => res.data);

export const getAgeGroupAnalysis = () =>
  apiClient.get("/api/analytics/age-group-analysis").then(res => res.data);

// ============================================================
//  PATIENTS
// ============================================================
export const getPatients = (limit = 20, offset = 0, search = "") => {
  const params = new URLSearchParams({ limit, offset });
  if (search) params.append("search", search);
  return apiClient.get(`/api/patients/?${params.toString()}`).then(res => res.data);
};

export const createPatient = (data) =>
  apiClient.post("/api/patients/", data).then(res => res.data);

export const updatePatient = (id, data) =>
  apiClient.put(`/api/patients/${id}`, data).then(res => res.data);

export const deletePatient = (id) =>
  apiClient.delete(`/api/patients/${id}`).then(res => res.data);

// ============================================================
//  HISTORY (Prediction Logs)
// ============================================================
export const getPredictionHistory = (limit = 20, offset = 0, disease = "") => {
  const params = new URLSearchParams({ limit, offset });
  if (disease) params.append("disease", disease);
  return apiClient.get(`/predict/history?${params.toString()}`).then(res => res.data);
};

// ---- Profile & Password ----
export const updateProfile = (username, email) =>
  apiClient.put("/auth/profile", { username, email }).then(res => res.data);

export const changePassword = (oldPassword, newPassword) =>
  apiClient.put("/auth/password", { old_password: oldPassword, new_password: newPassword })
    .then(res => res.data);

// ============================================================
//  REPORTS LIST
// ============================================================
export const listReports = (limit = 50, offset = 0) =>
  apiClient.get(`/api/reports/?limit=${limit}&offset=${offset}`).then(res => res.data);

// ============================================================
//  DEFAULT EXPORT
// ============================================================
export default apiClient;