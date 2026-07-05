/**
 * PatientForm.test.jsx
 * ----------------------
 * Basic React Testing Library tests for the PatientForm component:
 * required-field validation and successful submit calling onResult.
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import PatientForm from "../components/PatientForm";
import { predictDisease } from "../services/api";

jest.mock("../services/api");

describe("PatientForm", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders the Age field as required", () => {
    render(<PatientForm onResult={jest.fn()} />);
    expect(screen.getByText(/Age\*/i)).toBeInTheDocument();
  });

  test("shows a validation error when Age is missing on submit", async () => {
    render(<PatientForm onResult={jest.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /predict risk/i }));
    await waitFor(() => {
      expect(screen.getByText(/Age is required/i)).toBeInTheDocument();
    });
    expect(predictDisease).not.toHaveBeenCalled();
  });

  test("calls predictDisease and onResult on valid submit", async () => {
    const mockResponse = { results: { diabetes: {} } };
    predictDisease.mockResolvedValueOnce(mockResponse);
    const onResult = jest.fn();

    render(<PatientForm onResult={onResult} />);
    fireEvent.change(screen.getByLabelText(/^Age\*/i), { target: { value: "40" } });
    fireEvent.click(screen.getByRole("button", { name: /predict risk/i }));

    await waitFor(() => expect(predictDisease).toHaveBeenCalledTimes(1));
    expect(onResult).toHaveBeenCalledWith(
      mockResponse,
      expect.objectContaining({ age: 40 })
    );
  });

  test("shows server error message on API failure", async () => {
    predictDisease.mockRejectedValueOnce({
      response: { data: { error: "Backend exploded" } },
    });

    render(<PatientForm onResult={jest.fn()} />);
    fireEvent.change(screen.getByLabelText(/^Age\*/i), { target: { value: "40" } });
    fireEvent.click(screen.getByRole("button", { name: /predict risk/i }));

    await waitFor(() => {
      expect(screen.getByText(/Backend exploded/i)).toBeInTheDocument();
    });
  });
});
