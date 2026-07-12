/**
 * Analytics.jsx
 * -------------
 * Full analytics page with system statistics, model performance,
 * risk distribution, and prediction trends.
 */

import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import "../styles/Analytics.css";

// Helper to get auth token
const getAuthToken = () => localStorage.getItem("authToken");

// Axios instance with auth header
const apiClient = axios.create({
  baseURL: "/api/analytics",
});

apiClient.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default function Analytics() {
  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data states with safe defaults
  const [summary, setSummary] = useState({
    totalPredictions: 0,
    totalUsers: 0,
    predictionsThisMonth: 0,
    avgPredictionsPerUser: 0,
    diseaseBreakdown: {},
    modelUsage: {},
  });

  const [dailyData, setDailyData] = useState([]);
  const [modelPerformance, setModelPerformance] = useState([]);
  const [riskDistribution, setRiskDistribution] = useState({
    lowRisk: { count: 0, percentage: 0 },
    mediumRisk: { count: 0, percentage: 0 },
    highRisk: { count: 0, percentage: 0 },
    total: 0,
  });
  const [ageGroupData, setAgeGroupData] = useState([]);

  // Colors for charts
  const COLORS = {
    heart: "#ef4444",
    diabetes: "#3b82f6",
    hypertension: "#f59e0b",
    lowRisk: "#10b981",
    mediumRisk: "#f59e0b",
    highRisk: "#ef4444",
  };

  // Fetch all data
  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setError(null);

      try {
        const [
          summaryRes,
          dailyRes,
          modelRes,
          riskRes,
          ageRes,
        ] = await Promise.all([
          apiClient.get("/summary"),
          apiClient.get("/predictions-by-date?days=30"),
          apiClient.get("/model-performance"),
          apiClient.get("/risk-distribution"),
          apiClient.get("/age-group-analysis"),
        ]);

        if (summaryRes.data.success) setSummary(summaryRes.data.data);
        if (dailyRes.data.success) setDailyData(dailyRes.data.data);
        if (modelRes.data.success) setModelPerformance(modelRes.data.data);
        if (riskRes.data.success) setRiskDistribution(riskRes.data.data);
        if (ageRes.data.success) setAgeGroupData(ageRes.data.data);
      } catch (err) {
        setError(err.message || "Failed to load analytics data");
        console.error("Analytics fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, []);

  // ---- SAFE DATA TRANSFORMS ----
  // Disease breakdown – fallback to empty array
  const diseaseBreakdown = summary.diseaseBreakdown || {};
  const diseasePieData = Object.entries(diseaseBreakdown).map(([name, value]) => ({
    name,
    value,
    color: COLORS[name.toLowerCase()] || "#6b7280",
  }));

  // Model usage – fallback to empty array
  const modelUsage = summary.modelUsage || {};
  const modelUsageData = Object.entries(modelUsage).map(([name, value]) => ({
    name,
    value,
  }));

  // Risk distribution – safe access with defaults
  const lowRisk = riskDistribution?.lowRisk || { count: 0, percentage: 0 };
  const mediumRisk = riskDistribution?.mediumRisk || { count: 0, percentage: 0 };
  const highRisk = riskDistribution?.highRisk || { count: 0, percentage: 0 };
  const totalRisk = riskDistribution?.total ?? 0;

  const riskPieData = [
    { name: "Low Risk", value: lowRisk.count, color: COLORS.lowRisk },
    { name: "Medium Risk", value: mediumRisk.count, color: COLORS.mediumRisk },
    { name: "High Risk", value: highRisk.count, color: COLORS.highRisk },
  ];

  // ---- LOADING / ERROR STATES ----
  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="spinner" />
        <p>Loading analytics…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-error">
        <p>⚠️ {error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  // ---- RENDER ----
  return (
    <div className="analytics-page">
      <div className="page-header">
        <h1>Analytics</h1>
        <p>System analytics and statistics</p>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="summary-icon">📊</div>
          <div className="summary-content">
            <span className="summary-value">{summary.totalPredictions?.toLocaleString() || 0}</span>
            <span className="summary-label">Total Predictions</span>
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-icon">👥</div>
          <div className="summary-content">
            <span className="summary-value">{summary.totalUsers?.toLocaleString() || 0}</span>
            <span className="summary-label">Total Users</span>
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-icon">📅</div>
          <div className="summary-content">
            <span className="summary-value">{summary.predictionsThisMonth?.toLocaleString() || 0}</span>
            <span className="summary-label">Predictions This Month</span>
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-icon">📈</div>
          <div className="summary-content">
            <span className="summary-value">{summary.avgPredictionsPerUser?.toFixed(1) || "0.0"}</span>
            <span className="summary-label">Avg Predictions / User</span>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        {/* Daily Predictions Line Chart */}
        <div className="chart-card">
          <h3>Daily Predictions (Last 30 Days)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: "#3b82f6", r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Disease Breakdown Pie */}
        <div className="chart-card">
          <h3>Disease Breakdown</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={diseasePieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {diseasePieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Model Usage Bar */}
        <div className="chart-card">
          <h3>Model Usage</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={modelUsageData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Distribution Pie */}
        <div className="chart-card">
          <h3>Risk Level Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={riskPieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {riskPieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="risk-stats">
            <span>Total: {totalRisk}</span>
            <span>Low: {lowRisk.percentage}%</span>
            <span>Medium: {mediumRisk.percentage}%</span>
            <span>High: {highRisk.percentage}%</span>
          </div>
        </div>

        {/* Model Performance Table */}
        <div className="chart-card full-width">
          <h3>Model Performance Metrics</h3>
          <div className="model-table-wrapper">
            <table className="model-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Total Predictions</th>
                  <th>High Risk Cases</th>
                  <th>Accuracy (%)</th>
                  <th>Precision (%)</th>
                  <th>Recall (%)</th>
                  <th>F1 Score (%)</th>
                </tr>
              </thead>
              <tbody>
                {modelPerformance.length > 0 ? (
                  modelPerformance.map((model) => (
                    <tr key={model.model}>
                      <td>{model.model}</td>
                      <td>{model.totalPredictions}</td>
                      <td>{model.highRiskCases}</td>
                      <td>{model.accuracy}</td>
                      <td>{model.precision}</td>
                      <td>{model.recall}</td>
                      <td>{model.f1Score}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" style={{ textAlign: "center", color: "#6b7280" }}>
                      No model performance data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Age Group Analysis */}
        <div className="chart-card full-width">
          <h3>Age Group Analysis</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={ageGroupData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="group" />
              <YAxis yAxisId="left" orientation="left" stroke="#3b82f6" />
              <YAxis yAxisId="right" orientation="right" stroke="#ef4444" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="predictions" fill="#3b82f6" name="Predictions" />
              <Bar yAxisId="right" dataKey="avgRisk" fill="#ef4444" name="Average Risk" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}