"""
logistic_regression.py
-----------------------
Train a Logistic Regression classifier per disease using GridSearchCV over
C, solver, and penalty. Applies SMOTE to the training split to address
class imbalance. Saves the best estimator with joblib.

Run with:
    python -m src.models.logistic_regression
"""

import os

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from src.preprocessing.dataset import make_train_test_split
from src.utils.config import (
    GRID_SEARCH_CV_FOLDS,
    DISEASES,
    LOGISTIC_REGRESSION_PARAM_GRID,
    MODELS_DIR,
    PROCESSED_PATHS,
    RANDOM_SEED,
    TARGET_COLUMN,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def train_logistic_regression(disease: str):
    """
    Load processed data for `disease`, run GridSearchCV over a Logistic
    Regression hyperparameter grid, and save the best model.

    Returns:
        (best_estimator, X_test, y_test) for downstream evaluation.
    """
    logger.info(f"Training Logistic Regression for '{disease}'")
    df = pd.read_csv(PROCESSED_PATHS[disease])
    target_col = TARGET_COLUMN[disease]
    X = df.drop(columns=[target_col])
    y = df[target_col]

    X_train, X_test, y_train, y_test = make_train_test_split(X, y, apply_smote=True)

    cv = StratifiedKFold(
        n_splits=GRID_SEARCH_CV_FOLDS, shuffle=True, random_state=RANDOM_SEED
    )
    grid = GridSearchCV(
        estimator=LogisticRegression(random_state=RANDOM_SEED),
        param_grid=LOGISTIC_REGRESSION_PARAM_GRID,
        scoring="roc_auc",
        cv=cv,
        n_jobs=1,
    )
    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_
    logger.info(
        f"[{disease}] Best LR params: {grid.best_params_} | CV ROC-AUC: {grid.best_score_:.4f}"
    )

    model_path = os.path.join(MODELS_DIR, f"{disease}_logistic_regression.joblib")
    joblib.dump(best_model, model_path)
    logger.info(f"Saved Logistic Regression model -> {model_path}")

    return best_model, X_test, y_test


def main():
    results = {}
    for disease in DISEASES:
        results[disease] = train_logistic_regression(disease)
    return results


if __name__ == "__main__":
    main()
