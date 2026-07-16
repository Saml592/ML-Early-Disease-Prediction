/**
 * SignUp.jsx
 * ----------
 * User registration page with form validation and API integration.
 */

import React, { useState } from "react";
// import axios from "axios";
import "./Auth.css";
import { register } from "../services/api";

export default function SignUp({ onSignUpSuccess, onSwitchToSignIn }) {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError(""); // Clear error on input change
  };

  const validateForm = () => {
    if (!formData.username.trim()) {
      setError("Username is required");
      return false;
    }
    if (formData.username.length < 3) {
      setError("Username must be at least 3 characters");
      return false;
    }
    if (!formData.email.trim()) {
      setError("Email is required");
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError("Please enter a valid email address");
      return false;
    }
    if (!formData.password) {
      setError("Password is required");
      return false;
    }
    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters");
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
  e.preventDefault();

  if (!validateForm()) {
    return;
  }

  setLoading(true);
  setError("");

  try {
    // ✅ USE THE IMPORTED register FUNCTION
    const data = await register(
      formData.username,
      formData.email,
      formData.password
    );

    // data = { message, user, token }
    localStorage.setItem("authToken", data.token);
    localStorage.setItem("user", JSON.stringify(data.user));

    setSuccess(true);
    setFormData({
      username: "",
      email: "",
      password: "",
      confirmPassword: "",
    });

    if (onSignUpSuccess) {
      onSignUpSuccess(data.user);
    }

    setTimeout(() => {
      localStorage.removeItem("authToken");
      localStorage.removeItem("user");
      window.location.href = "/signin";
    }, 1500);
  } catch (err) {
    // err is the error object from Axios
    if (err.response?.data?.error) {
      setError(err.response.data.error);
    } else if (err.response?.data?.details) {
      setError(err.response.data.details[0]?.msg || "Registration failed");
    } else {
      setError("Registration failed. Please try again.");
    }
  } finally {
    setLoading(false);
  }
};

  if (success) {
    return (
      <div className="auth-container">
        <div className="auth-card success-card">
          <div className="success-icon">✓</div>
          <h2>Account Created Successfully!</h2>
          <p>Welcome to the Disease Prediction System.</p>
          <p className="redirect-text">Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Create Account</h1>
          <p>Join thousands of users getting personalized disease risk assessments</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="Choose a username"
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="your@email.com"
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="At least 6 characters"
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Re-enter your password"
              disabled={loading}
              required
            />
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? "Creating Account..." : "Create Account"}
          </button>
        </form>

         <div className="auth-footer">
        <p>
          Already have an account?{" "}
          <button
            type="button"
            onClick={onSwitchToSignIn}
            className="link-button"
          >
            Sign In
          </button>
        </p>
      </div>

        <div className="auth-benefits">
          <h3>Why Join?</h3>
          <ul>
            <li>✓ Advanced ML Models (Logistic Regression, Random Forest, Neural Network)</li>
            <li>✓ SHAP Explainability - Understand your risk factors</li>
            <li>✓ PDF Reports - Download detailed assessments</li>
            <li>✓ Secure & Private - Your health data is encrypted</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
