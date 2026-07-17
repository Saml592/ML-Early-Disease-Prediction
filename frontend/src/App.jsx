/**
 * App.jsx
 * -------
 * Main app component with sidebar, top navigation, and routing.
 */

import React, { useState } from "react";
import { useAuth } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
import TopNavigation from "./components/TopNavigation";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Reports from "./pages/Reports";
import History from "./pages/History";
import Patients from "./pages/Patients";
import LandingPage from "./pages/LandingPage";
import ExplainableAI from "./pages/ExplainableAI";
import Settings from "./pages/Settings";
import PatientForm from "./components/PatientForm";
import PredictionResult from "./components/PredictionResult";
import "./styles/App.css";

export default function App() {
  const { isAuthenticated, user, logout, loading } = useAuth();
  const [currentPage, setCurrentPage] = useState("landing");
  const [predictionData, setPredictionData] = useState(null);
  const [patientPayload, setPatientPayload] = useState(null);

  const handleResult = (data, payload) => {
    setPredictionData(data);
    setPatientPayload(payload);
  };

  const handleLogout = () => {
  logout();                  // clears localStorage and context state
  setCurrentPage("signin");  // navigate to sign-in without reload
};

  const handleSearch = (query) => {
    console.log("Search query:", query);
    // Implement search functionality
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

   if (!isAuthenticated) {
    // Landing page is the default
    if (currentPage === "landing") {
      return (
        <LandingPage
          onGetStarted={() => setCurrentPage("signin")}
        />
      );
    }
    // Sign-up page
    if (currentPage === "signup") {
      return (
        <SignUp
          onSignUpSuccess={() => setCurrentPage("dashboard")}
          onSwitchToSignIn={() => setCurrentPage("signin")}
        />
      );
    }
    // Default: show sign-in page (with link to sign-up)
    return (
  <SignIn
    onSignInSuccess={() => setCurrentPage("dashboard")}
    onSwitchToSignUp={() => setCurrentPage("signup")}
    onSwitchToLanding={() => setCurrentPage("landing")}   // <-- add this
  />
);
  }

  // Authenticated Routes with Sidebar Layout
  return (
    <ProtectedRoute>
      <div className="app-layout">
        <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
        <TopNavigation user={user} onLogout={handleLogout} onSearch={handleSearch} />

        <main className="app-content">
          {currentPage === "dashboard" && <Dashboard />}

          {currentPage === "prediction" && (
            <div className="page-container">
              <div className="page-header">
                <h1>Disease Prediction</h1>
                <p>Enter patient information to predict disease risk</p>
              </div>
              <div className="prediction-layout">
                <section className="prediction-form-section">
                  <h2>Patient Information</h2>
                  <PatientForm onResult={handleResult} />
                </section>

                <section className="prediction-results-section">
                  <h2>Prediction Results</h2>
                  {!predictionData && (
                    <div className="empty-state">
                      <p>Submit the form to see risk predictions.</p>
                    </div>
                  )}
                  <PredictionResult data={predictionData} patientPayload={patientPayload} />
                </section>
              </div>
            </div>
          )}

          {currentPage === "history" && (
            <div className="page-container">
              <div className="page-header">
                <h1>Prediction History</h1>
                <p>View all past predictions and results</p>
              </div>
              <div className="history-placeholder">
                <p>Prediction history </p>
              </div>
            </div>
          )}

          {currentPage === "patients" && (
            <div className="page-container">
              <div className="page-header">
                <h1>Patients</h1>
                <p>Manage patient records and information</p>
              </div>
              <div className="patients-placeholder">
                <p>Patient management </p>
              </div>
            </div>
          )}

          {currentPage === "reports" && (
            <div className="page-container">
              <div className="page-header">
                <h1>Reports</h1>
                <p>View and download prediction reports</p>
              </div>
              <div className="reports-placeholder">
                <p>Reports</p>
              </div>
            </div>
          )}

          {currentPage === "analytics" && (
            <div className="page-container">
              <div className="page-header">
                <h1>Analytics</h1>
                <p>System analytics and statistics</p>
              </div>
              <div className="analytics-placeholder">
                <p>Analytics</p>
              </div>
            </div>
          )}

          {currentPage === "explainable-ai" && (
            <div className="page-container">
              <div className="page-header">
                <h1>Explainable AI (SHAP)</h1>
                <p>Understand model predictions with SHAP explanations</p>
              </div>
              <div className="explainable-ai-placeholder">
                <p>SHAP explanations</p>
              </div>
            </div>
          )}

          {currentPage === "analytics" && <Analytics />}
          {currentPage === "reports" && <Reports />}
          {currentPage === "history" && <History />}
          {currentPage === "patients" && <Patients />}
          {currentPage === "explainable-ai" && <ExplainableAI />}
          {currentPage === "settings" && <Settings />}

          {/* {currentPage === "settings" && (
            <div className="page-container">
              <div className="page-header">
                <h1>Settings</h1>
                <p>System settings and configuration</p>
              </div>
              <div className="settings-placeholder">
                <p> </p>
              </div>
            </div>
          )} */}
        </main>
      </div>
    </ProtectedRoute>
  );
}
