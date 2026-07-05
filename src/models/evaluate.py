"""
evaluate.py
-----------
Shared evaluation utilities for all three model types (Logistic
Regression, Random Forest, ANN). Computes accuracy, precision, recall,
F1, and AUC-ROC; produces classification reports; plots/saves ROC curves;
and provides a 10-fold cross-validation helper for the sklearn-based
models (the ANN is evaluated via its held-out test set + KerasTuner's
internal validation split, since native Keras models don't plug directly
into sklearn's `cross_val_score`).
"""

import os

import matplotlib

matplotlib.use("Agg")  # headless backend, safe for server-side / CI use
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score  # noqa: E402

from src.utils.config import CV_FOLDS, DOCS_DIR, RANDOM_SEED  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def get_predictions(model, X_test, model_type: str = "sklearn"):
    """
    Return (y_pred_binary, y_pred_proba) for either a sklearn-style model
    or a Keras model, normalizing the differing predict() output shapes.
    """
    if model_type == "keras":
        y_pred_proba = model.predict(X_test, verbose=0).ravel()
    else:
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred_binary = (y_pred_proba >= 0.5).astype(int)
    return y_pred_binary, y_pred_proba


def compute_metrics(y_true, y_pred_binary, y_pred_proba) -> dict:
    """Compute the standard classification metric suite."""
    return {
        "accuracy": accuracy_score(y_true, y_pred_binary),
        "precision": precision_score(y_true, y_pred_binary, zero_division=0),
        "recall": recall_score(y_true, y_pred_binary, zero_division=0),
        "f1": f1_score(y_true, y_pred_binary, zero_division=0),
        "auc_roc": roc_auc_score(y_true, y_pred_proba),
    }


def get_classification_report(y_true, y_pred_binary) -> str:
    """Return a formatted sklearn classification report string."""
    return classification_report(
        y_true, y_pred_binary, target_names=["Not at Risk", "At Risk"]
    )


def plot_roc_curve(y_true, y_pred_proba, label: str, save_path: str = None):
    """Plot (and optionally save) an ROC curve for a single model."""
    fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
    auc = roc_auc_score(y_true, y_pred_proba)

    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f"{label} (AUC = {auc:.3f})")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Chance")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(f"ROC Curve - {label}")
    plt.legend(loc="lower right")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        logger.info(f"Saved ROC curve -> {save_path}")
    plt.close()


def cross_validate_sklearn_model(model, X, y, cv_folds: int = CV_FOLDS) -> dict:
    """
    Run `cv_folds`-fold stratified cross-validation for a sklearn-style
    model and return mean +/- std of ROC-AUC and accuracy.
    """
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_SEED)
    auc_scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc", n_jobs=1)
    acc_scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy", n_jobs=1)

    return {
        "cv_auc_mean": float(np.mean(auc_scores)),
        "cv_auc_std": float(np.std(auc_scores)),
        "cv_accuracy_mean": float(np.mean(acc_scores)),
        "cv_accuracy_std": float(np.std(acc_scores)),
    }


def evaluate_model(
    model,
    X_test,
    y_test,
    label: str,
    model_type: str = "sklearn",
    save_roc: bool = True,
) -> dict:
    """
    End-to-end evaluation: predictions -> metrics -> classification report
    -> ROC curve plot. Returns a dict combining all results.
    """
    y_pred_binary, y_pred_proba = get_predictions(model, X_test, model_type)
    metrics = compute_metrics(y_test, y_pred_binary, y_pred_proba)
    report = get_classification_report(y_test, y_pred_binary)

    logger.info(
        f"[{label}] Metrics: " + ", ".join(f"{k}={v:.4f}" for k, v in metrics.items())
    )
    logger.info(f"[{label}] Classification report:\n{report}")

    roc_path = None
    if save_roc:
        roc_path = os.path.join(
            DOCS_DIR, f"roc_curve_{label.replace(' ', '_').lower()}.png"
        )
        plot_roc_curve(y_test, y_pred_proba, label, save_path=roc_path)

    return {
        "label": label,
        "metrics": metrics,
        "classification_report": report,
        "roc_curve_path": roc_path,
    }
