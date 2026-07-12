/**
 * Sidebar.jsx
 * -----------
 * Left sidebar navigation for the hospital dashboard.
 */

import React, { useState } from "react";
import {
  LayoutDashboard,
  Users,
  Activity,
  History,
  FileText,
  BarChart3,
  Brain,
  Settings,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import "../styles/Sidebar.css";

export default function Sidebar({ currentPage, onNavigate }) {
  const [expandedMenus, setExpandedMenus] = useState({});

  const toggleMenu = (menuName) => {
    setExpandedMenus((prev) => ({
      ...prev,
      [menuName]: !prev[menuName],
    }));
  };

  const menuItems = [
    {
      label: "Dashboard",
      icon: LayoutDashboard,
      page: "dashboard",
      submenu: null,
    },
    {
      label: "Patients",
      icon: Users,
      page: "patients",
      submenu: [
        { label: "All Patients", page: "patients" },
        { label: "Add Patient", page: "add-patient" },
      ],
    },
    {
      label: "Disease Prediction",
      icon: Activity,
      page: "prediction",
      submenu: null,
    },
    {
      label: "Prediction History",
      icon: History,
      page: "history",
      submenu: null,
    },
    {
      label: "Reports",
      icon: FileText,
      page: "reports",
      submenu: null,
    },
    {
      label: "Analytics",
      icon: BarChart3,
      page: "analytics",
      submenu: null,
    },
    {
      label: "Explainable AI",
      icon: Brain,
      page: "explainable-ai",
      submenu: null,
    },
    {
      label: "Settings",
      icon: Settings,
      page: "settings",
      submenu: null,
    },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-container">
          <div className="logo-icon">🏥</div>
          <div className="logo-text">
            <h2>MediAI</h2>
            <p>Disease Prediction</p>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = currentPage === item.page;
          const isExpanded = expandedMenus[item.label];

          return (
            <div key={index} className="menu-item-wrapper">
              <button
                className={`menu-item ${isActive ? "active" : ""}`}
                onClick={() => {
                  if (item.submenu) {
                    toggleMenu(item.label);
                  } else {
                    onNavigate(item.page);
                  }
                }}
              >
                <Icon size={20} className="menu-icon" />
                <span className="menu-label">{item.label}</span>
                {item.submenu && (
                  <span className="menu-toggle">
                    {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                  </span>
                )}
              </button>

              {item.submenu && isExpanded && (
                <div className="submenu">
                  {item.submenu.map((subitem, subindex) => (
                    <button
                      key={subindex}
                      className={`submenu-item ${
                        currentPage === subitem.page ? "active" : ""
                      }`}
                      onClick={() => onNavigate(subitem.page)}
                    >
                      {subitem.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-info">
          <p>Hospital Management System</p>
          <span>v1.0</span>
        </div>
      </div>
    </aside>
  );
}
