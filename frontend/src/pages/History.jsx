/**
 * History.jsx
 * -----------
 * Prediction history page with paginated list of predictions.
 */

import React, { useState, useEffect } from "react";
import axios from "axios";
import "../styles/History.css";

const getAuthToken = () => localStorage.getItem("authToken");

const apiClient = axios.create({
  baseURL: "/predict",  // matches the backend blueprint prefix
});

apiClient.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

export default function History() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [diseaseFilter, setDiseaseFilter] = useState("");

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit,
        offset,
      });
      if (diseaseFilter) params.append("disease", diseaseFilter);
      const res = await apiClient.get(`/history?${params.toString()}`);
      if (res.data.success) {
        setPredictions(res.data.data.data);
        setTotal(res.data.data.total);
      } else {
        setError(res.data.error || "Failed to load history");
      }
    } catch (err) {
      setError(err.message || "Network error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [limit, offset, diseaseFilter]);

  const handlePrevPage = () => {
    if (offset - limit >= 0) setOffset(offset - limit);
  };

  const handleNextPage = () => {
    if (offset + limit < total) setOffset(offset + limit);
  };

  const handleFilterChange = (e) => {
    setDiseaseFilter(e.target.value);
    setOffset(0);
  };

  if (loading) {
    return (
      <div className="history-loading">
        <div className="spinner" />
        <p>Loading history…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="history-error">
        <p>⚠️ {error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="history-page">
      <div className="page-header">
        <h1>Prediction History</h1>
        <p>View all past predictions and results</p>
      </div>

      <div className="history-controls">
        <label>
          Filter by Disease:
          <select value={diseaseFilter} onChange={handleFilterChange}>
            <option value="">All</option>
            <option value="diabetes">Diabetes</option>
            <option value="heart">Cardiovascular Disease</option>
            <option value="hypertension">Hypertension</option>
          </select>
        </label>
        <span>Total: {total} entries</span>
      </div>

      {predictions.length === 0 ? (
        <div className="history-empty">
          <p>No predictions found.</p>
        </div>
      ) : (
        <div className="history-table-wrapper">
          <table className="history-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Disease</th>
                <th>Risk (%)</th>
                <th>Prediction</th>
                <th>Model</th>
                <th>Endpoint</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {predictions.map((p) => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{p.disease}</td>
                  <td>{(p.risk_probability * 100).toFixed(1)}%</td>
                  <td>
                    <span className={`risk-badge ${p.prediction_label === "At Risk" ? "high" : "low"}`}>
                      {p.prediction_label}
                    </span>
                  </td>
                  <td>{p.model_used}</td>
                  <td>{p.endpoint}</td>
                  <td>{new Date(p.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="history-pagination">
            <button onClick={handlePrevPage} disabled={offset === 0}>
              Previous
            </button>
            <span>Page {Math.floor(offset / limit) + 1} of {Math.ceil(total / limit)}</span>
            <button onClick={handleNextPage} disabled={offset + limit >= total}>
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}