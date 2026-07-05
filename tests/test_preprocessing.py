"""
test_preprocessing.py
-----------------------
Unit tests for the cleaning and feature-selection pipeline.
"""

import numpy as np
import pandas as pd
import pytest

from src.preprocessing.clean_data import load_and_clean
from src.preprocessing.feature_selection import correlation_filter, rfe_select
from src.utils.config import DISEASES, TARGET_COLUMN


@pytest.mark.parametrize("disease", DISEASES)
def test_load_and_clean_returns_no_nans(disease):
    X, y, scaler, encoders = load_and_clean(disease)
    assert X.isna().sum().sum() == 0
    assert y.isna().sum() == 0


@pytest.mark.parametrize("disease", DISEASES)
def test_load_and_clean_scaling_range(disease):
    X, y, scaler, encoders = load_and_clean(disease)
    assert (X.min() >= -1e-9).all()
    assert (X.max() <= 1 + 1e-9).all()


@pytest.mark.parametrize("disease", DISEASES)
def test_load_and_clean_target_is_binary(disease):
    X, y, scaler, encoders = load_and_clean(disease)
    assert set(y.unique()).issubset({0, 1})


def test_correlation_filter_drops_redundant_feature():
    rng = np.random.default_rng(0)
    base = rng.normal(size=200)
    df = pd.DataFrame(
        {
            "a": base,
            "b": base + rng.normal(scale=0.001, size=200),  # near-duplicate of 'a'
            "c": rng.normal(size=200),
        }
    )
    kept = correlation_filter(df, threshold=0.95)
    assert "c" in kept
    assert len(kept) == 2  # one of a/b dropped


def test_rfe_select_respects_n_features():
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.normal(size=(100, 8)), columns=[f"f{i}" for i in range(8)])
    y = pd.Series((X["f0"] + X["f1"] > 0).astype(int))
    selected = rfe_select(X, y, n_features=3)
    assert len(selected) == 3
    assert set(selected).issubset(set(X.columns))
