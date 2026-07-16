"""
shap_explainer.py
-------------------
Provides SHAP-based explainability for all three model types:
  - Random Forest      -> shap.TreeExplainer (fast, exact for tree ensembles)
  - Logistic Regression -> shap.LinearExplainer
  - ANN (Keras MLP)     -> shap.KernelExplainer with a small background sample
                            (model-agnostic, required since ANN has no
                            tree/linear structure SHAP can exploit directly)

`explain_prediction(model, model_type, input_data, feature_names,
background_data)` returns a dict mapping each feature name to its SHAP
value and percentage contribution to the prediction, plus the SHAP base
(expected) value and the final predicted probability.
"""

import numpy as np
import pandas as pd
import shap

from src.utils.logger import get_logger

logger = get_logger(__name__)

# KernelExplainer is expensive; cap background sample size for ANN models.
KERNEL_BACKGROUND_SIZE = 50


def _get_explainer(model, model_type: str, background_data: pd.DataFrame = None):
    """
    Build (or reuse) the appropriate SHAP explainer for a given model type.

    Args:
        model: Trained model object (sklearn estimator or Keras model).
        model_type: One of 'random_forest', 'logistic_regression', 'ann'.
        background_data: Required for 'logistic_regression' (masker) and
            'ann' (KernelExplainer background); a representative sample of
            training data (already preprocessed/scaled).
    """
    if model_type == "random_forest":
        return shap.TreeExplainer(model)

    if model_type == "logistic_regression":
        if background_data is None:
            raise ValueError("background_data is required for LinearExplainer")
        return shap.LinearExplainer(model, background_data)

    if model_type == "ann":
        if background_data is None:
            raise ValueError("background_data is required for KernelExplainer")
        bg_sample = shap.sample(
            background_data, min(KERNEL_BACKGROUND_SIZE, len(background_data))
        )

        def predict_fn(data):
            return model.predict(np.asarray(data, dtype=np.float32), verbose=0).ravel()

        return shap.KernelExplainer(predict_fn, bg_sample)

    raise ValueError(f"Unknown model_type '{model_type}'")


def explain_prediction(
    model,
    model_type: str,
    input_data: pd.DataFrame,
    feature_names: list[str],
    background_data: pd.DataFrame = None,
) -> dict:
    """
    Compute SHAP values for a single (or small batch of) prediction(s) and
    return a structured explanation.

    Args:
        model: Trained model (sklearn estimator or Keras model).
        model_type: 'random_forest' | 'logistic_regression' | 'ann'.
        input_data: DataFrame (1 row expected) of already-preprocessed
            (scaled, encoded, feature-selected) patient data.
        feature_names: Ordered list of feature names matching input_data columns.
        background_data: Reference/background dataset, required for
            'logistic_regression' and 'ann' explainer types.

    Returns:
        {
            "base_value": float,
            "predicted_probability": float,
            "feature_contributions": {
                feature_name: {
                    "shap_value": float,
                    "contribution_pct": float,  # percentage of total |SHAP| mass
                    "feature_value": float,
                },
                ...
            }
        }
    """
    explainer = _get_explainer(model, model_type, background_data)

    if model_type == "random_forest":
        raw_shap = explainer.shap_values(input_data)
        # shap.TreeExplainer on binary-classification RandomForest returns
        # a list [class_0_values, class_1_values] in older API styles, or
        # a single 3D array (n_samples, n_features, n_classes) in newer
        # ones. Normalize to the "class 1" (At Risk) contribution row.
        if isinstance(raw_shap, list):
            shap_values = raw_shap[1][0]
            base_value = explainer.expected_value[1]
        elif raw_shap.ndim == 3:
            shap_values = raw_shap[0, :, 1]
            base_value = explainer.expected_value[1]
        else:
            shap_values = raw_shap[0]
            base_value = explainer.expected_value
    elif model_type == "logistic_regression":
        shap_values = explainer.shap_values(input_data)[0]
        base_value = explainer.expected_value
    elif model_type == "ann":
        raw_shap = explainer.shap_values(input_data, nsamples=100, silent=True)
        shap_values = np.asarray(raw_shap).reshape(-1)
        base_value = (
            explainer.expected_value[0]
            if hasattr(explainer.expected_value, "__len__")
            else explainer.expected_value
        )
    else:
        raise ValueError(f"Unknown model_type '{model_type}'")

    base_value = float(np.asarray(base_value).ravel()[0])
    shap_values = np.asarray(shap_values, dtype=float).ravel()

    total_abs = np.sum(np.abs(shap_values)) or 1e-9  # avoid div-by-zero
    input_row = input_data.iloc[0]

    feature_contributions = {}
    for name, value, raw_value in zip(feature_names, shap_values, input_row.values):
        feature_contributions[name] = {
            "shap_value": float(value),
            "contribution_pct": float(abs(value) / total_abs * 100),
            "feature_value": float(raw_value),
        }

    predicted_probability = float(np.clip(base_value + np.sum(shap_values), 0.0, 1.0))
    if model_type == "logistic_regression":
        # LinearExplainer (interventional) explains the model's raw linear
        # decision function (log-odds), not predict_proba directly. Convert
        # the reconstructed log-odds back to a probability via sigmoid.
        logit_sum = base_value + np.sum(shap_values)
        predicted_probability = float(1.0 / (1.0 + np.exp(-logit_sum)))

    logger.info(
        f"SHAP explanation computed for model_type={model_type}; "
        f"base={base_value:.4f}, predicted={predicted_probability:.4f}"
    )

    return {
        "base_value": base_value,
        "predicted_probability": predicted_probability,
        "feature_contributions": feature_contributions,
    }
