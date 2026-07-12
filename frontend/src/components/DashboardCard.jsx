/**
 * DashboardCard.jsx
 * ----------------
 * Reusable card component for displaying dashboard metrics.
 */

import React from "react";
import "../styles/DashboardCard.css";

export default function DashboardCard({
  title,
  value,
  icon,
  trend,
  trendValue,
  borderColor = "border-blue",
}) {
  return (
    <div className={`dashboard-card ${borderColor}`}>
      <div className="card-header">
        <div className="card-icon">{icon}</div>
        <h3 className="card-title">{title}</h3>
      </div>

      <div className="card-value">{value}</div>

      {trend && (
        <div className={`card-trend ${trend === "up" ? "positive" : "negative"}`}>
          <span className="trend-icon">{trend === "up" ? "↑" : "↓"}</span>
          <span className="trend-text">{trendValue}</span>
        </div>
      )}
    </div>
  );
}
