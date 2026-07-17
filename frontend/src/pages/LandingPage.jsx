/**
 * LandingPage.jsx
 * ---------------
 * Public landing page with hero section, features, and call-to-action.
 */

import React from "react";
import "../styles/LandingPage.css";

export default function LandingPage({ onGetStarted }) {
  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1>Early Disease Prediction with AI</h1>
          <p className="hero-subtitle">
            Leverage machine learning to assess your risk for diabetes,
            cardiovascular disease, and hypertension with explainable insights.
          </p>
          <button className="cta-button" onClick={onGetStarted}>
            Get Started
          </button>
        </div>
        <div className="hero-image">
          <div className="hero-icon">🧬</div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <h2>Why Choose MediAI?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>Multiple ML Models</h3>
            <p>Logistic Regression, Random Forest, and Neural Network – each prediction is cross‑validated.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>Explainable AI (SHAP)</h3>
            <p>Understand which factors contribute most to your risk with SHAP feature‑importance charts.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📄</div>
            <h3>PDF Reports</h3>
            <p>Generate comprehensive, printable reports with all prediction details and SHAP visuals.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔒</div>
            <h3>Secure & Private</h3>
            <p>Your data is encrypted and never shared with third parties. JWT authentication keeps your account safe.</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <p>&copy; {new Date().getFullYear()} MediAI – Early Disease Prediction System</p>
        <p className="disclaimer">
          <strong>Disclaimer:</strong> This tool is for educational/demonstration purposes only and is not a substitute for professional medical advice.
        </p>
      </footer>
    </div>
  );
}