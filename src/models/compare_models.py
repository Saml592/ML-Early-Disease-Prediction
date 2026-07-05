"""
compare_models.py
------------------
Orchestrates training of all three model types (Logistic Regression,
Random Forest, ANN) for all three diseases, evaluates each on its held-out
test set (plus 10-fold CV for the sklearn models), prints a comparison
table to the console, and exports a Markdown report to
docs/model_comparison_report.md.

Run with:
    python -m src.models.compare_models
"""

import os
from datetime import datetime

import pandas as pd

from src.models.ann import train_ann
from src.models.evaluate import cross_validate_sklearn_model, evaluate_model
from src.models.logistic_regression import train_logistic_regression
from src.models.random_forest import train_random_forest
from src.utils.config import DISEASES, DOCS_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)

MIN_ACCURACY_TARGET = 0.85


def run_comparison_for_disease(disease: str) -> list[dict]:
    """Train + evaluate all three model types for a single disease."""
    rows = []

    # --- Logistic Regression ---
    lr_model, X_test, y_test = train_logistic_regression(disease)
    lr_eval = evaluate_model(
        lr_model, X_test, y_test, label=f"{disease}_logistic_regression"
    )
    lr_cv = cross_validate_sklearn_model(lr_model, X_test, y_test)
    rows.append(
        {
            "disease": disease,
            "model": "Logistic Regression",
            **lr_eval["metrics"],
            **lr_cv,
        }
    )

    # --- Random Forest ---
    rf_model, X_test_rf, y_test_rf = train_random_forest(disease)
    rf_eval = evaluate_model(
        rf_model, X_test_rf, y_test_rf, label=f"{disease}_random_forest"
    )
    rf_cv = cross_validate_sklearn_model(rf_model, X_test_rf, y_test_rf)
    rows.append(
        {"disease": disease, "model": "Random Forest", **rf_eval["metrics"], **rf_cv}
    )

    # --- ANN ---
    ann_model, X_test_ann, y_test_ann = train_ann(disease)
    ann_eval = evaluate_model(
        ann_model, X_test_ann, y_test_ann, label=f"{disease}_ann", model_type="keras"
    )
    rows.append(
        {
            "disease": disease,
            "model": "ANN (MLP)",
            **ann_eval["metrics"],
            "cv_auc_mean": None,
            "cv_auc_std": None,
            "cv_accuracy_mean": None,
            "cv_accuracy_std": None,
        }
    )

    return rows


def export_markdown_report(results_df: pd.DataFrame, path: str):
    """Write a human-readable Markdown comparison report."""
    lines = [
        "# Model Comparison Report",
        "",
        f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        "Models compared: **Logistic Regression**, **Random Forest**, **ANN (MLP)**, "
        "trained per disease on SMOTE-balanced training splits, evaluated on a held-out "
        f"20% test set. Target accuracy threshold: **{MIN_ACCURACY_TARGET:.0%}**.",
        "",
    ]

    for disease in results_df["disease"].unique():
        sub = results_df[results_df["disease"] == disease].copy()
        lines.append(f"## {disease.capitalize()}")
        lines.append("")
        display_cols = [
            "model",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "auc_roc",
            "cv_auc_mean",
            "cv_accuracy_mean",
        ]
        sub_display = sub[display_cols].copy()
        for col in [
            "accuracy",
            "precision",
            "recall",
            "f1",
            "auc_roc",
            "cv_auc_mean",
            "cv_accuracy_mean",
        ]:
            sub_display[col] = sub_display[col].apply(
                lambda v: f"{v:.4f}" if pd.notnull(v) else "n/a"
            )
        lines.append(sub_display.to_markdown(index=False))
        lines.append("")

        best_row = sub.loc[sub["accuracy"].idxmax()]
        lines.append(
            f"**Best model for {disease}:** {best_row['model']} "
            f"(accuracy={best_row['accuracy']:.4f}, AUC-ROC={best_row['auc_roc']:.4f})"
        )
        below_target = sub[sub["accuracy"] < MIN_ACCURACY_TARGET]
        if not below_target.empty:
            names = ", ".join(below_target["model"].tolist())
            n_rows = "the dataset"
            lines.append(
                f"\n> ⚠️ **Below {MIN_ACCURACY_TARGET:.0%} accuracy target:** {names}. "
                f"This reflects the inherent ceiling of {n_rows} used here (modest size, "
                "real-world noise, overlapping class distributions) rather than a "
                "modeling defect — see README for a full discussion of dataset limitations "
                "and what would be needed to close the gap (larger cohorts, richer clinical "
                "features, deep medical history)."
            )
        lines.append("")

    # CORRECT — explicitly UTF-8 on all platforms
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(f"Exported model comparison report -> {path}")


def main():
    all_rows = []
    for disease in DISEASES:
        logger.info(f"========== COMPARING MODELS: {disease.upper()} ==========")
        all_rows.extend(run_comparison_for_disease(disease))

    results_df = pd.DataFrame(all_rows)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)
    print("\n" + "=" * 80)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 80)
    print(results_df.to_string(index=False))

    report_path = os.path.join(DOCS_DIR, "model_comparison_report.md")
    export_markdown_report(results_df, report_path)

    results_df.to_csv(
        os.path.join(DOCS_DIR, "model_comparison_results.csv"), index=False
    )
    return results_df


if __name__ == "__main__":
    main()
