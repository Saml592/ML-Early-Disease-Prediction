"""
ann.py
------
Defines a 3-hidden-layer MLP (128, 64, 32 units, ReLU, Dropout 0.3) in
Keras for binary disease risk classification. Uses KerasTuner
(RandomSearch) to tune units/dropout/learning rate, trains with early
stopping, and saves the best model in HDF5 (.h5) format.

Run with:
    python -m src.models.ann
"""

import os

import keras_tuner as kt
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

from src.preprocessing.dataset import build_tf_datasets, make_train_test_split
from src.utils.config import (
    ANN_CONFIG,
    ANN_TUNER_CONFIG,
    DISEASES,
    MODELS_DIR,
    PROCESSED_PATHS,
    RANDOM_SEED,
    TARGET_COLUMN,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

tf.random.set_seed(RANDOM_SEED)


def build_model(hp: kt.HyperParameters, input_dim: int) -> keras.Model:
    """
    Build a 3-hidden-layer MLP with tunable units, dropout, and learning
    rate. Default search space is centered on the spec'd 128/64/32
    architecture and 0.3 dropout, per ANN_CONFIG.
    """
    units_1 = hp.Int("units_1", min_value=64, max_value=160, step=32, default=128)
    units_2 = hp.Int("units_2", min_value=32, max_value=96, step=16, default=64)
    units_3 = hp.Int("units_3", min_value=16, max_value=48, step=8, default=32)
    dropout_rate = hp.Float(
        "dropout_rate", min_value=0.1, max_value=0.5, step=0.1, default=0.3
    )
    learning_rate = hp.Choice("learning_rate", values=[1e-2, 1e-3, 1e-4], default=1e-3)

    model = keras.Sequential(
        [
            layers.Input(shape=(input_dim,)),
            layers.Dense(units_1, activation="relu"),
            layers.Dropout(dropout_rate),
            layers.Dense(units_2, activation="relu"),
            layers.Dropout(dropout_rate),
            layers.Dense(units_3, activation="relu"),
            layers.Dropout(dropout_rate),
            layers.Dense(1, activation="sigmoid"),
        ]
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=[
            keras.metrics.AUC(name="auc"),
            keras.metrics.Precision(name="precision"),
            keras.metrics.Recall(name="recall"),
            "accuracy",
        ],
    )
    return model


def train_ann(disease: str):
    """
    Load processed data for `disease`, tune an MLP architecture with
    KerasTuner RandomSearch, retrain the best configuration with early
    stopping, and save the model as .h5.

    Returns:
        (best_model, X_test, y_test)
    """
    logger.info(f"Training ANN for '{disease}'")
    df = pd.read_csv(PROCESSED_PATHS[disease])
    target_col = TARGET_COLUMN[disease]
    X = df.drop(columns=[target_col])
    y = df[target_col]

    X_train, X_test, y_train, y_test = make_train_test_split(X, y, apply_smote=True)
    input_dim = X_train.shape[1]

    tuner_dir = os.path.join(MODELS_DIR, "kt_tuning", disease)
    os.makedirs(tuner_dir, exist_ok=True)

    tuner = kt.RandomSearch(
        hypermodel=lambda hp: build_model(hp, input_dim),
        objective=kt.Objective("val_auc", direction="max"),
        max_trials=ANN_TUNER_CONFIG["max_trials"],
        executions_per_trial=ANN_TUNER_CONFIG["executions_per_trial"],
        directory=tuner_dir,
        project_name="ann_search",
        overwrite=True,
        seed=RANDOM_SEED,
    )

    early_stop_search = keras.callbacks.EarlyStopping(
        monitor="val_auc", mode="max", patience=5, restore_best_weights=True
    )

    logger.info(
        f"[{disease}] Starting KerasTuner search "
        f"({ANN_TUNER_CONFIG['max_trials']} trials)"
    )
    tuner.search(
        X_train,
        y_train,
        epochs=ANN_TUNER_CONFIG["epochs"],
        validation_split=0.2,
        callbacks=[early_stop_search],
        verbose=0,
    )

    best_hp = tuner.get_best_hyperparameters(num_trials=1)[0]
    logger.info(f"[{disease}] Best hyperparameters: {best_hp.values}")

    # Retrain final model on full training set with the best hyperparameters
    final_model = build_model(best_hp, input_dim)
    early_stop_final = keras.callbacks.EarlyStopping(
        monitor="val_auc",
        mode="max",
        patience=ANN_CONFIG["early_stopping_patience"],
        restore_best_weights=True,
    )
    history = final_model.fit(
        X_train,
        y_train,
        validation_split=0.2,
        epochs=ANN_CONFIG["epochs"],
        batch_size=ANN_CONFIG["batch_size"],
        callbacks=[early_stop_final],
        verbose=0,
    )

    final_val_auc = max(history.history.get("val_auc", [0.0]))
    logger.info(
        f"[{disease}] Final ANN training complete. Best val_auc={final_val_auc:.4f}"
    )

    model_path = os.path.join(MODELS_DIR, f"{disease}_ann.h5")
    final_model.save(model_path)
    logger.info(f"Saved ANN model -> {model_path}")

    return final_model, X_test, y_test


def main():
    results = {}
    for disease in DISEASES:
        results[disease] = train_ann(disease)
    return results


if __name__ == "__main__":
    main()
