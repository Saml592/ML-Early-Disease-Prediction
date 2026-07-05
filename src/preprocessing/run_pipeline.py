"""
run_pipeline.py
----------------
Main preprocessing entry point. For each disease:
    1. Load & clean raw data (impute, encode, scale)
    2. Run feature selection (correlation filter + RFE)
    3. Save the processed (selected-feature) DataFrame, including the
       target column, to data/processed/

Also persists the fitted scaler and encoders (per disease) to
models/saved/ via joblib, so the Flask API can apply identical
preprocessing to incoming patient data at inference time.

Run with:
    python -m src.preprocessing.run_pipeline
"""

import os

import joblib

from src.preprocessing.clean_data import load_and_clean
from src.preprocessing.feature_selection import select_features
from src.utils.config import DISEASES, MODELS_DIR, PROCESSED_PATHS, TARGET_COLUMN
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_for_disease(disease: str):
    logger.info(f"===== Preprocessing pipeline: {disease.upper()} =====")
    X, y, scaler, encoders = load_and_clean(disease)

    selected_features = select_features(X, y, disease)
    X_selected = X[selected_features]

    # Persist preprocessing artifacts for reuse by the API at inference time
    joblib.dump(scaler, os.path.join(MODELS_DIR, f"{disease}_scaler.joblib"))
    joblib.dump(encoders, os.path.join(MODELS_DIR, f"{disease}_encoders.joblib"))
    joblib.dump(
        selected_features,
        os.path.join(MODELS_DIR, f"{disease}_selected_features.joblib"),
    )

    processed_df = X_selected.copy()
    processed_df[TARGET_COLUMN[disease]] = y.values
    processed_df.to_csv(PROCESSED_PATHS[disease], index=False)

    logger.info(
        f"Saved processed '{disease}' data -> {PROCESSED_PATHS[disease]} "
        f"({processed_df.shape[0]} rows, {len(selected_features)} selected features)"
    )
    return processed_df


def main():
    results = {}
    for disease in DISEASES:
        results[disease] = run_for_disease(disease)
    logger.info("Preprocessing pipeline complete for all diseases.")
    return results


if __name__ == "__main__":
    main()
