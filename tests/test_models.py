"""
test_models.py
----------------
Sanity tests on trained model artifacts: prediction output shapes and
value ranges. Assumes the training pipeline has already been run (i.e.
models/saved/*.joblib and *.h5 exist) — see README for how to generate
them via `python -m src.models.compare_models`.
"""

import os

import joblib
import numpy as np
import pandas as pd
import pytest

from src.utils.config import DISEASES, MODELS_DIR, PROCESSED_PATHS, TARGET_COLUMN

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(MODELS_DIR, "diabetes_random_forest.joblib")),
    reason="Trained models not found; run `python -m src.models.compare_models` first.",
)


@pytest.mark.parametrize("disease", DISEASES)
def test_random_forest_predict_proba_shape(disease):
    model = joblib.load(os.path.join(MODELS_DIR, f"{disease}_random_forest.joblib"))
    selected_features = joblib.load(
        os.path.join(MODELS_DIR, f"{disease}_selected_features.joblib")
    )
    df = pd.read_csv(PROCESSED_PATHS[disease])
    X = df[selected_features].iloc[:5]

    proba = model.predict_proba(X)
    assert proba.shape == (5, 2)
    assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-6)
    assert (proba >= 0).all() and (proba <= 1).all()


@pytest.mark.parametrize("disease", DISEASES)
def test_logistic_regression_predict_proba_shape(disease):
    model = joblib.load(
        os.path.join(MODELS_DIR, f"{disease}_logistic_regression.joblib")
    )
    selected_features = joblib.load(
        os.path.join(MODELS_DIR, f"{disease}_selected_features.joblib")
    )
    df = pd.read_csv(PROCESSED_PATHS[disease])
    X = df[selected_features].iloc[:5]

    proba = model.predict_proba(X)
    assert proba.shape == (5, 2)


@pytest.mark.parametrize("disease", DISEASES)
def test_ann_predict_shape_and_range(disease):
    import tensorflow as tf

    model = tf.keras.models.load_model(os.path.join(MODELS_DIR, f"{disease}_ann.h5"))
    selected_features = joblib.load(
        os.path.join(MODELS_DIR, f"{disease}_selected_features.joblib")
    )
    df = pd.read_csv(PROCESSED_PATHS[disease])
    X = df[selected_features].iloc[:5].values.astype(np.float32)

    preds = model.predict(X, verbose=0)
    assert preds.shape == (5, 1)
    assert (preds >= 0).all() and (preds <= 1).all()
