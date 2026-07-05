/**
 * PredictionResult.test.jsx
 * ---------------------------
 * Tests that PredictionResult renders per-disease cards with risk
 * percentages and outcome labels from a mock /predict response.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import PredictionResult from "../components/PredictionResult";

const mockData = {
  results: {
    diabetes: {
      random_forest: {
        risk_probability_pct: 72.5,
        prediction: "At Risk",
        confidence_threshold: 0.5,
      },
      logistic_regression: {
        risk_probability_pct: 30.1,
        prediction: "Not at Risk",
        confidence_threshold: 0.5,
      },
    },
  },
  errors: {},
};

describe("PredictionResult", () => {
  test("renders nothing when data is null", () => {
    const { container } = render(
      <PredictionResult data={null} patientPayload={{}} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  test("renders disease card with risk percentages and outcomes", () => {
    render(<PredictionResult data={mockData} patientPayload={{ age: 40 }} />);
    expect(screen.getByText(/Diabetes/i)).toBeInTheDocument();
    expect(screen.getByText(/72.5%/)).toBeInTheDocument();
    expect(screen.getByText(/At Risk/)).toBeInTheDocument();
    expect(screen.getByText(/Not at Risk/)).toBeInTheDocument();
  });

  test("renders an Explain button per model result", () => {
    render(<PredictionResult data={mockData} patientPayload={{ age: 40 }} />);
    const explainButtons = screen.getAllByRole("button", { name: /explain/i });
    expect(explainButtons).toHaveLength(2);
  });
});
