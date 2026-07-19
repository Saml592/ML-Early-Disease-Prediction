/**
 * Patients.jsx
 * ------------
 * Patient management with CRUD operations.
 */

import React, { useState, useEffect } from "react";
import apiClient from "../services/api";
import "../styles/Patients.css";

// apiClient is imported from services/api — uses Render backend in production


// ---- Modal component for Add/Edit ----
function PatientModal({ isOpen, onClose, patient, onSubmit, loading }) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    age: "",
    gender: "",
    medical_history: "",
  });

  useEffect(() => {
    if (patient) {
      setForm({
        name: patient.name || "",
        email: patient.email || "",
        phone: patient.phone || "",
        age: patient.age || "",
        gender: patient.gender || "",
        medical_history: patient.medical_history || "",
      });
    } else {
      setForm({ name: "", email: "", phone: "", age: "", gender: "", medical_history: "" });
    }
  }, [patient]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(form);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>{patient ? "Edit Patient" : "Add New Patient"}</h2>
        <form onSubmit={handleSubmit}>
          <label>
            Name*
            <input type="text" name="name" value={form.name} onChange={handleChange} required />
          </label>
          <label>
            Email*
            <input type="email" name="email" value={form.email} onChange={handleChange} required />
          </label>
          <label>
            Phone
            <input type="text" name="phone" value={form.phone} onChange={handleChange} />
          </label>
          <label>
            Age
            <input type="number" name="age" value={form.age} onChange={handleChange} />
          </label>
          <label>
            Gender
            <select name="gender" value={form.gender} onChange={handleChange}>
              <option value="">Select</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </label>
          <label>
            Medical History
            <textarea name="medical_history" value={form.medical_history} onChange={handleChange} />
          </label>
          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button type="submit" disabled={loading}>
              {loading ? "Saving..." : patient ? "Update" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Patients() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [patients, setPatients] = useState([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editingPatient, setEditingPatient] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit, offset });
      if (search) params.append("search", search);
      const res = await apiClient.get(`/api/patients/?${params.toString()}`);
      if (res.data.success) {
        setPatients(res.data.data.data);
        setTotal(res.data.data.total);
      } else {
        setError(res.data.error || "Failed to load patients");
      }
    } catch (err) {
      setError(err.message || "Network error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
  const fetchPatients = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit, offset });
      if (search) params.append("search", search);
      const res = await apiClient.get(`/api/patients/?${params.toString()}`);
      if (res.data.success) {
        setPatients(res.data.data.data);
        setTotal(res.data.data.total);
      } else {
        setError(res.data.error || "Failed to load patients");
      }
    } catch (err) {
      setError(err.message || "Network error");
    } finally {
      setLoading(false);
    }
  };
  fetchPatients();
}, [limit, offset, search]);

  const handleSearch = (e) => {
    setSearch(e.target.value);
    setOffset(0);
  };

  const handlePrevPage = () => {
    if (offset - limit >= 0) setOffset(offset - limit);
  };

  const handleNextPage = () => {
    if (offset + limit < total) setOffset(offset + limit);
  };

  const openAddModal = () => {
    setEditingPatient(null);
    setShowModal(true);
  };

  const openEditModal = (patient) => {
    setEditingPatient(patient);
    setShowModal(true);
  };

  const handleSubmit = async (formData) => {
    setSubmitting(true);
    try {
      if (editingPatient) {
        await apiClient.put(`/api/patients/${editingPatient.id}`, formData);
      } else {
        await apiClient.post("/api/patients/", formData);
      }
      setShowModal(false);
      fetchPatients();
    } catch (err) {
      alert(err.response?.data?.error || "Operation failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (patient) => {
    if (!window.confirm(`Delete patient "${patient.name}"?`)) return;
    try {
      await apiClient.delete(`/api/patients/${patient.id}`);
      fetchPatients();
    } catch (err) {
      alert(err.response?.data?.error || "Delete failed");
    }
  };

  if (loading) {
    return (
      <div className="patients-loading">
        <div className="spinner" />
        <p>Loading patients…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="patients-error">
        <p>⚠️ {error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="patients-page">
      <div className="page-header">
        <h1>Patients</h1>
        <p>Manage patient records and information</p>
      </div>

      <div className="patients-controls">
        <div className="patients-actions">
          <button className="add-btn" onClick={openAddModal}>+ Add Patient</button>
          <input
            type="text"
            placeholder="Search patients..."
            value={search}
            onChange={handleSearch}
            className="search-input"
          />
        </div>
        <span>Total: {total} patients</span>
      </div>

      {patients.length === 0 ? (
        <div className="patients-empty">
          <p>No patients found. Add your first patient!</p>
        </div>
      ) : (
        <div className="patients-table-wrapper">
          <table className="patients-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Medical History</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((p) => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{p.name}</td>
                  <td>{p.email}</td>
                  <td>{p.phone || "—"}</td>
                  <td>{p.age || "—"}</td>
                  <td>{p.gender || "—"}</td>
                  <td>{p.medical_history || "—"}</td>
                  <td>
                    <button className="edit-btn" onClick={() => openEditModal(p)}>✎ Edit</button>
                    <button className="delete-btn" onClick={() => handleDelete(p)}>🗑 Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="patients-pagination">
            <button onClick={handlePrevPage} disabled={offset === 0}>Previous</button>
            <span>Page {Math.floor(offset / limit) + 1} of {Math.ceil(total / limit)}</span>
            <button onClick={handleNextPage} disabled={offset + limit >= total}>Next</button>
          </div>
        </div>
      )}

      <PatientModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        patient={editingPatient}
        onSubmit={handleSubmit}
        loading={submitting}
      />
    </div>
  );
}