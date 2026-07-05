"""
clean_data.py
-------------
Load the three raw datasets (Pima Indians Diabetes, Cleveland Heart
Disease, Hypertension Risk), handle missing values via median imputation,
encode categorical variables, and apply Min-Max scaling.

Each `load_and_clean_<disease>` function returns:
    (X: pd.DataFrame, y: pd.Series, scaler: MinMaxScaler, encoders: dict)

so that the same scaler/encoders can later be reused at inference time in
the Flask API.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

from src.utils.config import (
    CATEGORICAL_COLUMNS,
    PIMA_COLUMNS,
    RAW_PATHS,
    TARGET_COLUMN,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _median_impute(df: pd.DataFrame, columns) -> pd.DataFrame:
    """Replace NaNs (and, for Pima-style data, biologically impossible 0s)
    in the given numeric columns with the column median."""
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            continue
        n_missing = df[col].isna().sum()
        if n_missing > 0:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.debug(
                f"Imputed {n_missing} missing values in '{col}' with median={median_val}"
            )
    return df


def _encode_categoricals(df: pd.DataFrame, columns) -> tuple[pd.DataFrame, dict]:
    """Label-encode categorical columns, returning the fitted encoders so
    the same mapping can be applied to new inference data."""
    df = df.copy()
    encoders = {}
    for col in columns:
        if col not in df.columns:
            continue
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
        logger.debug(f"Encoded '{col}' -> classes: {list(le.classes_)}")
    return df, encoders


def _scale_features(X: pd.DataFrame) -> tuple[pd.DataFrame, MinMaxScaler]:
    """Apply Min-Max scaling to all feature columns."""
    scaler = MinMaxScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)
    return X_scaled, scaler


def load_and_clean_diabetes() -> tuple[pd.DataFrame, pd.Series, MinMaxScaler, dict]:
    """
    Load and clean the Pima Indians Diabetes dataset.

    Notes:
        In this dataset, 0 is used as a placeholder for missing values in
        Glucose, BloodPressure, SkinThickness, Insulin, and BMI (a value of
        0 is not physiologically possible for these). These are treated as
        missing and median-imputed.
    """
    logger.info("Loading Pima Indians Diabetes dataset")
    df = pd.read_csv(RAW_PATHS["diabetes"], header=None, names=PIMA_COLUMNS)

    zero_as_missing_cols = [
        "Glucose",
        "BloodPressure",
        "SkinThickness",
        "Insulin",
        "BMI",
    ]
    for col in zero_as_missing_cols:
        df[col] = df[col].replace(0, np.nan)

    df = _median_impute(df, zero_as_missing_cols)

    target_col = TARGET_COLUMN["diabetes"]
    y = df[target_col].astype(int)
    X = df.drop(columns=[target_col])

    X_scaled, scaler = _scale_features(X)
    logger.info(
        f"Diabetes dataset cleaned: {X_scaled.shape[0]} rows, {X_scaled.shape[1]} features"
    )
    return X_scaled, y, scaler, {}


def load_and_clean_heart() -> tuple[pd.DataFrame, pd.Series, MinMaxScaler, dict]:
    """Load and clean the Cleveland Heart Disease dataset."""
    logger.info("Loading Cleveland Heart Disease dataset")
    df = pd.read_csv(RAW_PATHS["heart"])
    df.columns = [c.strip() for c in df.columns]

    target_col = TARGET_COLUMN["heart"]
    numeric_cols = [c for c in df.columns if c != target_col]
    df = _median_impute(df, numeric_cols)

    # In this dataset all columns are already numeric-coded categoricals,
    # but we still run them through the encoder step for consistency with
    # datasets that have true string categoricals.
    df, encoders = _encode_categoricals(df, CATEGORICAL_COLUMNS["heart"])

    y = df[target_col].astype(int)
    # Heart disease target in some versions of this dataset is 0-4 severity;
    # binarize to "any disease present" vs "no disease".
    y = (y > 0).astype(int)
    X = df.drop(columns=[target_col])

    X_scaled, scaler = _scale_features(X)
    logger.info(
        f"Heart dataset cleaned: {X_scaled.shape[0]} rows, {X_scaled.shape[1]} features"
    )
    return X_scaled, y, scaler, encoders


def load_and_clean_hypertension() -> tuple[pd.DataFrame, pd.Series, MinMaxScaler, dict]:
    """Load and clean the Hypertension Risk dataset."""
    logger.info("Loading Hypertension Risk dataset")
    df = pd.read_csv(RAW_PATHS["hypertension"])

    target_col = TARGET_COLUMN["hypertension"]
    numeric_cols = [
        c
        for c in df.columns
        if c not in CATEGORICAL_COLUMNS["hypertension"] + [target_col]
    ]
    df = _median_impute(df, numeric_cols)

    df, encoders = _encode_categoricals(df, CATEGORICAL_COLUMNS["hypertension"])

    y = df[target_col].astype(int)
    X = df.drop(columns=[target_col])

    X_scaled, scaler = _scale_features(X)
    logger.info(
        f"Hypertension dataset cleaned: {X_scaled.shape[0]} rows, {X_scaled.shape[1]} features"
    )
    return X_scaled, y, scaler, encoders


LOADERS = {
    "diabetes": load_and_clean_diabetes,
    "heart": load_and_clean_heart,
    "hypertension": load_and_clean_hypertension,
}


def load_and_clean(disease: str):
    """Dispatch helper: load_and_clean('diabetes' | 'heart' | 'hypertension')."""
    if disease not in LOADERS:
        raise ValueError(
            f"Unknown disease '{disease}'. Expected one of {list(LOADERS)}"
        )
    return LOADERS[disease]()
