/**
 * Settings.jsx
 * ------------
 * User settings: profile and password management.
 */

import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { updateProfile, changePassword } from "../services/api";
import "../styles/Settings.css";

export default function Settings() {
  const { user, login } = useAuth(); // removed 'logout' – it was unused
  const [activeTab, setActiveTab] = useState("profile");

  // ---- Profile state ----
  const [profileData, setProfileData] = useState({
    username: "",
    email: "",
  });
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileMessage, setProfileMessage] = useState({ text: "", type: "" });

  // ---- Password state ----
  const [passwordData, setPasswordData] = useState({
    oldPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState({ text: "", type: "" });

  // ---- Theme state (localStorage) ----
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("darkMode") === "true";
  });

  // Populate profile form when user changes
  useEffect(() => {
    if (user) {
      setProfileData({
        username: user.username || "",
        email: user.email || "",
      });
    }
  }, [user]);

  // ---- Apply theme class to body ----
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add("dark-mode");
    } else {
      document.body.classList.remove("dark-mode");
    }
  }, [darkMode]); // <-- added dependency

  // ---- Theme toggle ----
  const toggleTheme = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem("darkMode", String(newMode));
  };

  // ---- Profile update ----
  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileLoading(true);
    setProfileMessage({ text: "", type: "" });

    try {
      const result = await updateProfile(profileData.username, profileData.email);
      // Update user in context
      login(result.user, localStorage.getItem("authToken"));
      setProfileMessage({ text: "Profile updated successfully!", type: "success" });
    } catch (err) {
      const msg = err.response?.data?.error || "Update failed";
      setProfileMessage({ text: msg, type: "error" });
    } finally {
      setProfileLoading(false);
    }
  };

  // ---- Password change ----
  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordMessage({ text: "Passwords do not match", type: "error" });
      return;
    }
    if (passwordData.newPassword.length < 6) {
      setPasswordMessage({ text: "Password must be at least 6 characters", type: "error" });
      return;
    }
    setPasswordLoading(true);
    setPasswordMessage({ text: "", type: "" });

    try {
      await changePassword(passwordData.oldPassword, passwordData.newPassword);
      setPasswordMessage({ text: "Password changed successfully!", type: "success" });
      setPasswordData({ oldPassword: "", newPassword: "", confirmPassword: "" });
    } catch (err) {
      const msg = err.response?.data?.error || "Password change failed";
      setPasswordMessage({ text: msg, type: "error" });
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <p>System settings and configuration</p>
      </div>

      <div className="settings-tabs">
        <button
          className={activeTab === "profile" ? "active" : ""}
          onClick={() => setActiveTab("profile")}
        >
          Profile
        </button>
        <button
          className={activeTab === "security" ? "active" : ""}
          onClick={() => setActiveTab("security")}
        >
          Security
        </button>
        <button
          className={activeTab === "preferences" ? "active" : ""}
          onClick={() => setActiveTab("preferences")}
        >
          Preferences
        </button>
      </div>

      {/* Profile Tab */}
      {activeTab === "profile" && (
        <div className="settings-card">
          <h2>Profile Information</h2>
          <form onSubmit={handleProfileSubmit}>
            <label>
              Username
              <input
                type="text"
                value={profileData.username}
                onChange={(e) =>
                  setProfileData({ ...profileData, username: e.target.value })
                }
                required
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={profileData.email}
                onChange={(e) =>
                  setProfileData({ ...profileData, email: e.target.value })
                }
                required
              />
            </label>
            {profileMessage.text && (
              <div className={`settings-message ${profileMessage.type}`}>
                {profileMessage.text}
              </div>
            )}
            <button type="submit" disabled={profileLoading}>
              {profileLoading ? "Saving..." : "Update Profile"}
            </button>
          </form>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === "security" && (
        <div className="settings-card">
          <h2>Change Password</h2>
          <form onSubmit={handlePasswordSubmit}>
            <label>
              Current Password
              <input
                type="password"
                value={passwordData.oldPassword}
                onChange={(e) =>
                  setPasswordData({ ...passwordData, oldPassword: e.target.value })
                }
                required
              />
            </label>
            <label>
              New Password
              <input
                type="password"
                value={passwordData.newPassword}
                onChange={(e) =>
                  setPasswordData({ ...passwordData, newPassword: e.target.value })
                }
                required
              />
            </label>
            <label>
              Confirm New Password
              <input
                type="password"
                value={passwordData.confirmPassword}
                onChange={(e) =>
                  setPasswordData({ ...passwordData, confirmPassword: e.target.value })
                }
                required
              />
            </label>
            {passwordMessage.text && (
              <div className={`settings-message ${passwordMessage.type}`}>
                {passwordMessage.text}
              </div>
            )}
            <button type="submit" disabled={passwordLoading}>
              {passwordLoading ? "Changing..." : "Change Password"}
            </button>
          </form>
        </div>
      )}

      {/* Preferences Tab */}
      {activeTab === "preferences" && (
        <div className="settings-card">
          <h2>Appearance</h2>
          <div className="theme-toggle">
            <label>
              <input
                type="checkbox"
                checked={darkMode}
                onChange={toggleTheme}
              />
              Enable Dark Mode
            </label>
          </div>
          <p className="settings-note">
            Theme preference is saved in your browser.
          </p>
        </div>
      )}
    </div>
  );
}
