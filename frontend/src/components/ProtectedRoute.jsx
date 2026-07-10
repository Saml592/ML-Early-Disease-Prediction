/**
 * ProtectedRoute.jsx
 * ------------------
 * Higher-order component that protects routes by requiring authentication.
 * Redirects unauthenticated users to the sign-in page.
 */

import React from "react";
import { useAuth } from "../contexts/AuthContext";

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    window.location.href = "/signin";
    return null;
  }

  return children;
}
