"""
feature_selection.py
---------------------
Implements:
  1. Recursive Feature Elimination (RFE) using a RandomForestClassifier
     estimator to rank and select the top-K features per disease.
  2. A correlation-matrix filter that drops one feature from any pair with
     |correlation| above a configured threshold (to reduce multicollinearity
     before RFE runs).

`select_features(X, y, disease)` returns the filtered/selected list of
feature names, which is then used to subset the processed DataFrame.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE

from src.utils.config import (
    CORRELATION_THRESHOLD,
    RANDOM_SEED,
    RFE_N_FEATURES_TO_SELECT,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def correlation_filter(
    X: pd.DataFrame, threshold: float = CORRELATION_THRESHOLD
) -> list[str]:
    """
    Drop one feature from each pair of features whose absolute Pearson
    correlation exceeds `threshold`.

    Returns:
        List of column names to keep.
    """
    corr_matrix = X.corr().abs()
    upper_mask = np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    upper = corr_matrix.where(upper_mask)

    to_drop = set()
    for col in upper.columns:
        correlated_with = upper.index[upper[col] > threshold].tolist()
        for row in correlated_with:
            if row not in to_drop and col not in to_drop:
                to_drop.add(col)

    kept = [c for c in X.columns if c not in to_drop]
    if to_drop:
        logger.info(
            f"Correlation filter dropped {len(to_drop)} feature(s): {sorted(to_drop)}"
        )
    return kept


def rfe_select(X: pd.DataFrame, y: pd.Series, n_features: int) -> list[str]:
    """
    Run Recursive Feature Elimination with a RandomForestClassifier
    estimator to select the top `n_features` features.

    Returns:
        List of selected feature names, in their original column order.
    """
    n_features = min(n_features, X.shape[1])
    estimator = RandomForestClassifier(
        n_estimators=100, random_state=RANDOM_SEED, n_jobs=1
    )
    selector = RFE(estimator=estimator, n_features_to_select=n_features, step=1)
    selector.fit(X, y)
    selected = X.columns[selector.support_].tolist()
    logger.info(f"RFE selected {len(selected)} feature(s): {selected}")
    return selected


def select_features(X: pd.DataFrame, y: pd.Series, disease: str) -> list[str]:
    """
    Full feature selection pipeline for a given disease:
        1. Correlation filter to remove redundant features.
        2. RFE (Random Forest) to select the most predictive subset.

    Args:
        X: Cleaned, scaled feature DataFrame.
        y: Target Series.
        disease: One of 'diabetes', 'heart', 'hypertension'.

    Returns:
        Final list of selected feature names.
    """
    kept_after_corr = correlation_filter(X)
    X_filtered = X[kept_after_corr]

    n_features = RFE_N_FEATURES_TO_SELECT.get(disease, min(8, X_filtered.shape[1]))
    selected = rfe_select(X_filtered, y, n_features)
    return selected
