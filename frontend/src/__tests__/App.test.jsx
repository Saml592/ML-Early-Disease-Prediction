/**
 * App.test.jsx
 * ------------
 * Smoke tests: verifies the top-level App renders its header and sections.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import App from "../App";

jest.mock("../services/api");

describe("App", () => {
  test("renders the main title", () => {
    render(<App />);
    expect(
      screen.getByText(/ML-Powered Early Disease Prediction System/i)
    ).toBeInTheDocument();
  });

  test("renders the Patient Information section heading", () => {
    render(<App />);
    expect(screen.getByText(/Patient Information/i)).toBeInTheDocument();
  });

  test("renders the Prediction Results section heading", () => {
    render(<App />);
    expect(screen.getByText(/Prediction Results/i)).toBeInTheDocument();
  });

  test("renders the disclaimer footer", () => {
    render(<App />);
    expect(screen.getByText(/Disclaimer/i)).toBeInTheDocument();
  });
});
