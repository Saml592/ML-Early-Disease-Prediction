"""
dataset.py
----------
Builds tf.data.Dataset objects (and applies SMOTE oversampling on the
training split) for use by the ANN model. Kept separate from clean_data.py
so the ANN-specific data plumbing doesn't leak into the generic cleaning
pipeline used by the classical ML models.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split

from src.utils.config import RANDOM_SEED, TEST_SIZE
from src.utils.logger import get_logger

logger = get_logger(__name__)


def make_train_test_split(X: pd.DataFrame, y: pd.Series, apply_smote: bool = True):
    """
    Stratified train/test split, with optional SMOTE oversampling applied
    ONLY to the training set (never to the test set, to avoid leakage and
    to keep evaluation metrics representative of real-world class balance).

    Returns:
        X_train, X_test, y_train, y_test (all as numpy arrays)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=y
    )

    if apply_smote:
        before_counts = np.bincount(y_train)
        smote = SMOTE(random_state=RANDOM_SEED)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        after_counts = np.bincount(y_train)
        logger.info(
            f"SMOTE applied to training set: {before_counts.tolist()} -> {after_counts.tolist()}"
        )

        # SMOTE appends synthetic minority-class samples to the end of the
        # array. If left in this order, a downstream contiguous slice
        # (e.g. Keras' validation_split, which takes the tail of the
        # array) could end up single-class. Shuffle to avoid that.
        rng = np.random.default_rng(RANDOM_SEED)
        shuffle_idx = rng.permutation(len(X_train))
        X_train = np.asarray(X_train)[shuffle_idx]
        y_train = np.asarray(y_train)[shuffle_idx]

    return (
        np.asarray(X_train, dtype=np.float32),
        np.asarray(X_test, dtype=np.float32),
        np.asarray(y_train, dtype=np.float32),
        np.asarray(y_test, dtype=np.float32),
    )


def build_tf_datasets(X_train, X_test, y_train, y_test, batch_size: int = 32):
    """
    Wrap numpy arrays into tf.data.Dataset pipelines with shuffling,
    batching, and prefetching for efficient ANN training.
    """
    train_ds = (
        tf.data.Dataset.from_tensor_slices((X_train, y_train))
        .shuffle(buffer_size=len(X_train), seed=RANDOM_SEED)
        .batch(batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )
    test_ds = (
        tf.data.Dataset.from_tensor_slices((X_test, y_test))
        .batch(batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )
    return train_ds, test_ds
