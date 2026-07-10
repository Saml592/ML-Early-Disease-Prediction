/**
 * App.jsx
 * -------
 * Main app component with routing, authentication, and layout.
 */

import React, { useState } from "react";
import { useAuth } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";
import PatientForm from "./components/PatientForm";
import PredictionResult from "./components/PredictionResult";
import "./App.css";

export default function App() {
  const { isAuthenticated, user, logout, loading } = useAuth();
  const [predictionData, setPredictionData] = useState(null);
  const [patientPayload, setPatientPayload] = useState(null);
  const [currentPage, setCurrentPage] = useState("dashboard");

  const handleResult = (data, payload) => {
    setPredictionData(data);
    setPatientPayload(payload);
  };

  const handleLogout = () => {
    logout();
    window.location.href = "/signin";
  };

  // Show loading state
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Route: Sign In
if (currentPage === "signin" && !isAuthenticated) {
  return (
    <SignIn
      onSignInSuccess={() => setCurrentPage("dashboard")}
      onSwitchToSignUp={() => {    // <-- THIS MUST EXIST
        console.log("Switching to signup");
        setCurrentPage("signup");
      }}
    />
  );
}

  // Route: Sign Up
  if (currentPage === "signup" && !isAuthenticated) {
  return (
    <SignUp
      onSignUpSuccess={() => setCurrentPage("dashboard")}
      onSwitchToSignIn={() => setCurrentPage("signin")}   // <-- ADD THIS
    />
  );
}


  // Redirect to signin if not authenticated
if (!isAuthenticated) {
    return (
        <SignIn
            onSignInSuccess={() => setCurrentPage("dashboard")}
            onSwitchToSignUp={() => {
                console.log("Switching to signup from fallback");
                setCurrentPage("signup");
            }}
        />
    );
}

  // Route: Dashboard (Protected)
  return (
    <ProtectedRoute>
      <div className="app-container">
        <header className="app-header">
          <div className="header-left">
            <h1>ML-Powered Early Disease Prediction System</h1>
            <p>
              Estimate risk of diabetes, cardiovascular disease, and hypertension using
              Logistic Regression, Random Forest, and Neural Network models, with SHAP
              explainability.
            </p>
          </div>
          <div className="header-right">
            <div className="user-info">
              <span className="username">{user?.username}</span>
              <span className="email">{user?.email}</span>
            </div>
            <button className="logout-button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </header>

        <main className="app-main">
          <section className="form-section">
            <h2>Patient Information</h2>
            <PatientForm onResult={handleResult} />
          </section>

          <section className="results-section">
            <h2>Prediction Results</h2>
            {!predictionData && <p>Submit the form to see risk predictions.</p>}
            <PredictionResult data={predictionData} patientPayload={patientPayload} />
          </section>
        </main>

        <footer className="app-footer">
          <p>
            <strong>Disclaimer:</strong> This tool is for educational/demonstration purposes
            only and is not a substitute for professional medical advice, diagnosis, or
            treatment.
          </p>
        </footer>
      </div>
    </ProtectedRoute>
  );
}
