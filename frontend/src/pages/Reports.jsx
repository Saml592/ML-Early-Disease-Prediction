/**
 * Reports.jsx
 * -----------
 * List all generated reports with download/re‑generate options.
 */

import React, { useState, useEffect } from "react";
import apiClient from "../services/api";
import "../styles/Reports.css";

// apiClient is imported from services/api — uses Render backend in production


export default function Reports() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reports, setReports] = useState([]);

  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await apiClient.get("/api/reports/?limit=100");
        if (res.data.success) {
          setReports(res.data.data);
        } else {
          setError(res.data.error || "Failed to load reports");
        }
      } catch (err) {
        setError(err.message || "Network error");
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  const handleDownload = (reportRef) => {
    // For now, we don't have a way to re‑download the exact report without the patient data.
    // We could store the patient payload, but we don't. So we show a placeholder action.
    alert(`Re‑download report ${reportRef} – feature coming soon.`);
    // In the future, we could call a GET /reports/:ref/download to regenerate.
  };

  if (loading) {
    return (
      <div className="reports-loading">
        <div className="spinner" />
        <p>Loading reports…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="reports-error">
        <p>⚠️ {error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="reports-page">
      <div className="page-header">
        <h1>Reports</h1>
        <p>View and download previously generated prediction reports</p>
      </div>

      {reports.length === 0 ? (
        <div className="reports-empty">
          <p>No reports generated yet. Generate a report from the Prediction page.</p>
        </div>
      ) : (
        <div className="reports-table-wrapper">
          <table className="reports-table">
            <thead>
              <tr>
                <th>Report Reference</th>
                <th>Date</th>
                <th>Patient Age</th>
                <th>Diseases</th>
                <th>Model</th>
                <th>Status</th>
                <th>Format</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id}>
                  <td><strong>{report.report_ref}</strong></td>
                  <td>{new Date(report.timestamp).toLocaleString()}</td>
                  <td>{report.patient_age || "—"}</td>
                  <td>{report.diseases_included?.replace(/,/g, ", ") || "—"}</td>
                  <td>{report.model_type || "—"}</td>
                  <td>
                    <span className={`status-badge ${report.status === "success" ? "success" : "error"}`}>
                      {report.status}
                    </span>
                  </td>
                  <td>{report.format?.toUpperCase() || "—"}</td>
                  <td>
                    <button
                      className="download-btn"
                      onClick={() => handleDownload(report.report_ref)}
                      disabled={report.status !== "success"}
                    >
                      📄 Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}