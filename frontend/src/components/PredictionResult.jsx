/**
 * PredictionResult.jsx
 * ----------------------
 * Displays per-disease risk cards (gauge + outcome + Explain button).
 * Adds a "Download Report" button at the bottom that POSTs to /report,
 * receives a PDF blob, and triggers a browser download.
 */
import React, { useState } from "react";
import { downloadReport } from "../services/api";
import ShapChart from "./ShapChart";

const DISEASE_LABELS = {
  diabetes:     "Diabetes",
  heart:        "Cardiovascular Disease",
  hypertension: "Hypertension",
};

const MODEL_LABELS = {
  logistic_regression: "Logistic Regression",
  random_forest:       "Random Forest",
  ann:                 "Neural Network (ANN)",
};

// ── Sub-components ────────────────────────────────────────────────────────────

function RiskGauge({ pct, label }) {
  const color = pct >= 50 ? "#c62828" : "#2e7d32";
  return (
    <div className="risk-gauge">
      <div className="risk-gauge-label">
        <span>{label}</span>
        <span style={{ color, fontWeight: 700 }}>{pct.toFixed(1)}%</span>
      </div>
      <div className="risk-gauge-track">
        <div
          className="risk-gauge-fill"
          style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function DiseaseCard({ disease, modelResults, patientPayload }) {
  const [explainingModel, setExplainingModel] = useState(null);

  return (
    <div className="disease-card">
      <h3>{DISEASE_LABELS[disease] || disease}</h3>

      {Object.entries(modelResults).map(([modelType, result]) => {
        if (result.error) {
          return (
            <div key={modelType} className="model-result error">
              {MODEL_LABELS[modelType] || modelType}: {result.error}
            </div>
          );
        }
        return (
          <div key={modelType} className="model-result">
            <RiskGauge
              pct={result.risk_probability_pct}
              label={MODEL_LABELS[modelType] || modelType}
            />
            <div className="model-outcome">
              Outcome:{" "}
              <strong
                className={result.prediction === "At Risk" ? "at-risk" : "not-at-risk"}
              >
                {result.prediction}
              </strong>
              <button
                type="button"
                className="explain-btn"
                onClick={() =>
                  setExplainingModel(
                    explainingModel === modelType ? null : modelType
                  )
                }
              >
                {explainingModel === modelType ? "Hide Explanation" : "Explain"}
              </button>
            </div>

            {explainingModel === modelType && (
              <ShapChart
                disease={disease}
                modelType={modelType}
                patientPayload={patientPayload}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Download Report button ────────────────────────────────────────────────────

function DownloadReportButton({ data, patientPayload }) {
  const [downloading, setDownloading]       = useState(false);
  const [downloadError, setDownloadError]   = useState(null);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    setDownloadError(null);
    setDownloadSuccess(false);

    try {
      const { blob, filename } = await downloadReport(
        patientPayload,
        data.results   // pass pre-computed predictions so the server skips re-prediction
      );

      // Create a temporary object URL and click it to trigger the download
      const url  = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href     = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      // Revoke after a short delay to let the download start
      setTimeout(() => URL.revokeObjectURL(url), 5000);

      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 4000);
    } catch (err) {
      const msg =
        err?.response?.data instanceof Blob
          ? "Report generation failed. Check the server logs."
          : err?.response?.data?.error || err.message || "Download failed.";
      setDownloadError(msg);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="report-download-section">
      <button
        type="button"
        className="download-report-btn"
        onClick={handleDownload}
        disabled={downloading}
      >
        {downloading
          ? "⏳  Generating report…"
          : "📄  Download PDF Report"}
      </button>

      {downloadSuccess && (
        <p className="download-success">
          ✅ Report downloaded successfully.
        </p>
      )}
      {downloadError && (
        <p className="download-error">
          ⚠️ {downloadError}
        </p>
      )}

      <p className="report-disclaimer">
        The report embeds SHAP feature-importance charts and is intended as a
        clinical decision-support document, not a diagnosis.
      </p>
    </div>
  );
}

// ── Main exported component ───────────────────────────────────────────────────

export default function PredictionResult({ data, patientPayload }) {
  if (!data) return null;

  const { results = {}, errors = {} } = data;
  const hasResults = Object.keys(results).length > 0;

  return (
    <div className="prediction-results">
      {Object.entries(results).map(([disease, modelResults]) => (
        <DiseaseCard
          key={disease}
          disease={disease}
          modelResults={modelResults}
          patientPayload={patientPayload}
        />
      ))}

      {Object.entries(errors).map(([disease, message]) => (
        <div key={disease} className="disease-card error">
          <h3>{DISEASE_LABELS[disease] || disease}</h3>
          <p>{message}</p>
        </div>
      ))}

      {hasResults && (
        <DownloadReportButton data={data} patientPayload={patientPayload} />
      )}
    </div>
  );
}
