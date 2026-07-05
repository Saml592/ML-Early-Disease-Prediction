"""
utils.py
--------
Helpers for the Flask API:
  - Cached loading of trained models, scalers, encoders, and selected
    feature lists (saved by the training/preprocessing pipeline).
  - `build_model_input(disease, patient)`: maps a validated PatientData
    payload to the exact raw-column DataFrame the disease's scaler
    expects, applies categorical encoding + Min-Max scaling, then
    subsets to the RFE-selected features used at training time.
"""

import os

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf

from src.utils.config import CATEGORICAL_COLUMNS, MODELS_DIR, PIMA_COLUMNS
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Mapping from PatientData (snake_case API field names) to each disease's
# original raw column names (must exactly match what clean_data.py used,
# since the saved scaler/encoders were fit on those column names/order).
# ---------------------------------------------------------------------------
FEATURE_NAME_MAP = {
    "diabetes": {
        "pregnancies": "Pregnancies",
        "glucose": "Glucose",
        "blood_pressure": "BloodPressure",
        "skin_thickness": "SkinThickness",
        "insulin": "Insulin",
        "bmi": "BMI",
        "diabetes_pedigree_function": "DiabetesPedigreeFunction",
        "age": "Age",
    },
    "heart": {
        "age": "age",
        "sex": "sex",
        "cp": "cp",
        "blood_pressure": "trestbps",
        "cholesterol": "chol",
        "fbs": "fbs",
        "restecg": "restecg",
        "thalach": "thalach",
        "exang": "exang",
        "oldpeak": "oldpeak",
        "slope": "slope",
        "ca": "ca",
        "thal": "thal",
    },
    "hypertension": {
        "age": "Age",
        "bmi": "BMI",
        "sodium_intake": "SodiumIntake",
        "smoking_status": "SmokingStatus",
        "alcohol_units_week": "AlcoholUnitsWeek",
        "physical_activity_min_week": "PhysicalActivityMinWeek",
        "family_history": "FamilyHistory",
        "stress_score": "StressScore",
        "resting_heart_rate": "RestingHeartRate",
        "cholesterol": "Cholesterol",
        "glucose": "Glucose",
    },
}

RAW_COLUMN_ORDER = {
    "diabetes": PIMA_COLUMNS[:-1],  # exclude target
    "heart": [
        "age",
        "sex",
        "cp",
        "trestbps",
        "chol",
        "fbs",
        "restecg",
        "thalach",
        "exang",
        "oldpeak",
        "slope",
        "ca",
        "thal",
    ],
    "hypertension": [
        "Age",
        "BMI",
        "SodiumIntake",
        "SmokingStatus",
        "AlcoholUnitsWeek",
        "PhysicalActivityMinWeek",
        "FamilyHistory",
        "StressScore",
        "RestingHeartRate",
        "Cholesterol",
        "Glucose",
    ],
}

MODEL_FILENAMES = {
    "logistic_regression": "{disease}_logistic_regression.joblib",
    "random_forest": "{disease}_random_forest.joblib",
    "ann": "{disease}_ann.h5",
}

_CACHE = {}


def _cache_get_or_load(key, loader_fn):
    if key not in _CACHE:
        _CACHE[key] = loader_fn()
    return _CACHE[key]


def load_scaler(disease: str):
    path = os.path.join(MODELS_DIR, f"{disease}_scaler.joblib")
    return _cache_get_or_load(f"scaler:{disease}", lambda: joblib.load(path))


def load_encoders(disease: str) -> dict:
    path = os.path.join(MODELS_DIR, f"{disease}_encoders.joblib")
    return _cache_get_or_load(f"encoders:{disease}", lambda: joblib.load(path))


def load_selected_features(disease: str) -> list:
    path = os.path.join(MODELS_DIR, f"{disease}_selected_features.joblib")
    return _cache_get_or_load(f"selected_features:{disease}", lambda: joblib.load(path))


def load_model(disease: str, model_type: str):
    """Load (and cache) a trained model. model_type in
    {'logistic_regression', 'random_forest', 'ann'}."""
    if model_type not in MODEL_FILENAMES:
        raise ValueError(f"Unknown model_type '{model_type}'")

    filename = MODEL_FILENAMES[model_type].format(disease=disease)
    path = os.path.join(MODELS_DIR, filename)

    def _load():
        if model_type == "ann":
            return tf.keras.models.load_model(path)
        return joblib.load(path)

    return _cache_get_or_load(f"model:{disease}:{model_type}", _load)


def get_missing_required_fields(disease: str, patient_dict: dict) -> list:
    """Return the list of API field names required for `disease` that are
    None/missing in the given patient dict."""
    field_map = FEATURE_NAME_MAP[disease]
    missing = [
        api_field for api_field in field_map if patient_dict.get(api_field) is None
    ]
    return missing


def build_model_input(disease: str, patient_dict: dict) -> pd.DataFrame:
    """
    Convert a validated PatientData dict into a single-row DataFrame ready
    to feed into the trained model for `disease`:
        1. Map API field names -> original raw column names.
        2. Apply saved LabelEncoders to any categorical columns.
        3. Apply the saved MinMaxScaler (fit at training time) across all
           raw columns, in the exact order the scaler expects.
        4. Subset to the RFE-selected feature columns used at training time.

    Raises:
        ValueError if required fields for this disease are missing.
    """
    missing = get_missing_required_fields(disease, patient_dict)
    if missing:
        raise ValueError(
            f"Missing required field(s) for '{disease}' prediction: {missing}"
        )

    field_map = FEATURE_NAME_MAP[disease]
    raw_row = {
        raw_col: patient_dict[api_field] for api_field, raw_col in field_map.items()
    }

    raw_df = pd.DataFrame([raw_row])[RAW_COLUMN_ORDER[disease]]

    encoders = load_encoders(disease)
    for col in CATEGORICAL_COLUMNS.get(disease, []):
        if col in encoders and col in raw_df.columns:
            le = encoders[col]
            raw_df[col] = le.transform(raw_df[col].astype(str))

    scaler = load_scaler(disease)
    scaled_values = scaler.transform(raw_df)
    scaled_df = pd.DataFrame(scaled_values, columns=raw_df.columns)

    selected_features = load_selected_features(disease)
    model_input = scaled_df[selected_features]

    return model_input


def load_background_sample(disease: str, n: int = 100) -> pd.DataFrame:
    """
    Load a random sample of the processed (scaled, feature-selected)
    training data for `disease`, for use as the SHAP explainer background
    distribution (required by LinearExplainer and KernelExplainer).
    """
    from src.utils.config import PROCESSED_PATHS, TARGET_COLUMN

    def _load():
        df = pd.read_csv(PROCESSED_PATHS[disease])
        df = df.drop(columns=[TARGET_COLUMN[disease]])
        sample_n = min(n, len(df))
        return df.sample(sample_n, random_state=42).reset_index(drop=True)

    return _cache_get_or_load(f"background:{disease}:{n}", _load)


def predict_with_model(disease: str, model_type: str, model_input: pd.DataFrame):
    """
    Run inference with the given model type and return (probability,
    binary_label) where probability is the "At Risk" (positive class)
    probability in [0, 1].
    """
    model = load_model(disease, model_type)

    if model_type == "ann":
        proba = float(
            model.predict(model_input.values.astype(np.float32), verbose=0).ravel()[0]
        )
    else:
        proba = float(model.predict_proba(model_input)[:, 1][0])

    return proba
