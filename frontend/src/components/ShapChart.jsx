/**
 * ShapChart.jsx
 * --------------
 * Fetches SHAP explanation data for a given disease/model/patient and
 * renders a horizontal bar chart of feature contribution percentages
 * (using Recharts), along with the base value and final predicted
 * probability.
 */
import React, { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { explainDisease } from "../services/api";

export default function ShapChart({ disease, modelType, patientPayload }) {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    explainDisease(disease, patientPayload, modelType)
      .then((data) => {
        if (isMounted) setExplanation(data);
      })
      .catch((err) => {
        if (isMounted) {
          setError(err?.response?.data?.error || err.message || "Failed to load explanation");
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [disease, modelType, patientPayload]);

  if (loading) return <div className="shap-chart-loading">Loading explanation...</div>;
  if (error) return <div className="shap-chart-error">{error}</div>;
  if (!explanation) return null;

  const chartData = Object.entries(explanation.feature_contributions)
    .map(([feature, info]) => ({
      feature,
      contribution_pct: info.shap_value >= 0 ? info.contribution_pct : -info.contribution_pct,
      shap_value: info.shap_value,
    }))
    .sort((a, b) => Math.abs(b.contribution_pct) - Math.abs(a.contribution_pct));

  return (
    <div className="shap-chart">
      <div className="shap-summary">
        <span>Base value: {(explanation.base_value * 100).toFixed(1)}%</span>
        <span>Final prediction: {explanation.predicted_probability_pct}% ({explanation.prediction})</span>
      </div>
      <ResponsiveContainer width="100%" height={Math.max(200, chartData.length * 40)}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 30, right: 30 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" unit="%" />
          <YAxis type="category" dataKey="feature" width={140} />
          <Tooltip
            formatter={(value, name, props) => [
              `${props.payload.shap_value.toFixed(4)} (${Math.abs(value).toFixed(1)}% of total impact)`,
              "SHAP value",
            ]}
          />
          <Bar dataKey="contribution_pct">
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.shap_value >= 0 ? "#d9534f" : "#5cb85c"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="shap-legend">
        <span className="legend-red">■</span> increases risk &nbsp;
        <span className="legend-green">■</span> decreases risk
      </p>
    </div>
  );
}
