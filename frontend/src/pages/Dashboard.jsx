/**
 * Dashboard.jsx
 * -----------
 * Main dashboard page with metrics cards and analytics overview.
 * Fetches live data from the backend API.
 */

import React, { useState, useEffect } from "react";
import apiClient from "../services/api";
import DashboardCard from "../components/DashboardCard";
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
  ResponsiveContainer,
} from "recharts";
import "../styles/Dashboard.css";

// apiClient is imported from services/api — uses Render backend in production

export default function Dashboard() {
  // --- State ---
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [stats, setStats] = useState({
    totalPatients: 0,
    totalPredictions: 0,
    heartDisease: 0,
    diabetes: 0,
    hypertension: 0,
    avgAccuracy: 94.2, // placeholder
  });

  const [dailyData, setDailyData] = useState([]);
  const [diseaseDist, setDiseaseDist] = useState([]);
  const [riskDist, setRiskDist] = useState([]);
  const [monthlyAccuracy, setMonthlyAccuracy] = useState([]);

  // --- Color mapping for disease distribution ---
  const DISEASE_COLORS = {
    diabetes: "#3b82f6",    // blue
    heart: "#ef4444",       // red
    hypertension: "#f59e0b" // yellow
  };

  // --- Fetch functions ---
  const fetchMetrics = async () => {
    const res = await apiClient.get("/api/dashboard/metrics");
    if (res.data.success) {
      setStats(res.data.data);
    }
  };

  const fetchDailyPredictions = async () => {
    const res = await apiClient.get("/api/dashboard/daily-predictions");
    if (res.data.success) {
      setDailyData(res.data.data);
    }
  };

  const fetchDiseaseDistribution = async () => {
    const res = await apiClient.get("/api/dashboard/disease-distribution");
    if (res.data.success) {
      setDiseaseDist(res.data.data);
    }
  };

  const fetchRiskDistribution = async () => {
    const res = await apiClient.get("/api/dashboard/risk-distribution");
    if (res.data.success) {
      setRiskDist(res.data.data);
    }
  };

  const fetchMonthlyAccuracy = async () => {
    // This endpoint is mocked on the backend; we keep it as is
    const res = await apiClient.get("/api/dashboard/monthly-accuracy");
    if (res.data.success) {
      setMonthlyAccuracy(res.data.data);
    }
  };

  // --- Load all data ---
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        await Promise.all([
          fetchMetrics(),
          fetchDailyPredictions(),
          fetchDiseaseDistribution(),
          fetchRiskDistribution(),
          fetchMonthlyAccuracy(),
        ]);
      } catch (err) {
        setError(err.message || "Failed to load dashboard data");
        console.error("Dashboard fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // --- Loading & error states ---
  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner" />
        <p>Loading dashboard…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <p>⚠️ {error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  // --- Render ---
  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Welcome to the Disease Prediction Management System</p>
      </div>

      {/* Metrics Cards */}
      <div className="metrics-grid">
        <DashboardCard
          title="Total Patients"
          value={stats.totalPatients.toLocaleString()}
          icon="👥"
          trend="up"
          trendValue="Based on prediction logs"
          borderColor="border-yellow"
        />
        <DashboardCard
          title="Total Predictions"
          value={stats.totalPredictions.toLocaleString()}
          icon="📊"
          trend="up"
          trendValue="All-time"
          borderColor="border-green"
        />
        <DashboardCard
          title="Heart Disease Cases"
          icon="❤️"
          value={stats.heartDisease}
          trend="up"
          trendValue="Confirmed cases"
          borderColor="border-red"
        />
        <DashboardCard
          title="Diabetes Cases"
          icon="🩺"
          value={stats.diabetes}
          trend="up"
          trendValue="Confirmed cases"
          borderColor="border-blue"
        />
        <DashboardCard
          title="Hypertension Cases"
          icon="🩸"
          value={stats.hypertension}
          trend="down"
          trendValue="Confirmed cases"
          borderColor="border-purple"
        />
        <DashboardCard
          title="Average Accuracy"
          icon="🎯"
          value={`${stats.avgAccuracy}%`}
          trend="up"
          trendValue="Model performance"
          borderColor="border-indigo"
        />
      </div>

      {/* Charts Section */}
      <div className="charts-section">
        <div className="chart-container">
          <h2>Daily Predictions</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="predictions"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: "#3b82f6", r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h2>Disease Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={diseaseDist}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {diseaseDist.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={DISEASE_COLORS[entry.name?.toLowerCase()] || "#6b7280"}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="charts-section">
        <div className="chart-container">
          <h2>Risk Level Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={riskDist}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="level" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]}>
                {riskDist.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h2>Monthly Model Accuracy</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={monthlyAccuracy}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis domain={[90, 96]} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="accuracy"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: "#10b981", r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
