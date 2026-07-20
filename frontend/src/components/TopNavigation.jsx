/**
 * TopNavigation.jsx
 * -----------------
 * Top navigation bar with search, notifications, and user profile.
 */

import React, { useState } from "react";
import { Search, Bell, LogOut, User, Menu } from "lucide-react";
import "../styles/TopNavigation.css";

export default function TopNavigation({ user, onLogout, onSearch, onMenuToggle }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    if (onSearch) {
      onSearch(query);
    }
  };

  return (
    <header className="top-navigation">
      <div className="nav-left">
        <button className="hamburger-button" onClick={onMenuToggle}>
          <Menu size={20} />
        </button>
        <div className="search-container">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Search patients, predictions..."
            className="search-input"
            value={searchQuery}
            onChange={handleSearch}
          />
        </div>
      </div>

      <div className="nav-right">
        {/* Notifications */}
        <div className="notification-container">
          <button
            className="notification-button"
            onClick={() => setShowNotifications(!showNotifications)}
          >
            <Bell size={20} />
            <span className="notification-badge">3</span>
          </button>

          {showNotifications && (
            <div className="notification-dropdown">
              <div className="notification-item">
                <p className="notification-title">New prediction submitted</p>
                <p className="notification-time">5 minutes ago</p>
              </div>
              <div className="notification-item">
                <p className="notification-title">Patient record updated</p>
                <p className="notification-time">1 hour ago</p>
              </div>
              <div className="notification-item">
                <p className="notification-title">Report generated</p>
                <p className="notification-time">2 hours ago</p>
              </div>
            </div>
          )}
        </div>

        {/* User Profile */}
        <div className="user-profile-container">
          <button
            className="user-profile-button"
            onClick={() => setShowUserMenu(!showUserMenu)}
          >
            <div className="user-avatar">
              {user?.username?.charAt(0).toUpperCase() || "U"}
            </div>
            <div className="user-info">
              <p className="user-name">{user?.username || "User"}</p>
              <p className="user-role">Administrator</p>
            </div>
          </button>

          {showUserMenu && (
            <div className="user-menu-dropdown">
              <button className="user-menu-item">
                <User size={18} />
                <span>My Profile</span>
              </button>
              <hr className="menu-divider" />
              <button className="user-menu-item logout" onClick={onLogout}>
                <LogOut size={18} />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
