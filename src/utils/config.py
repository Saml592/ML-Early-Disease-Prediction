"""
config.py
---------
Single source of truth for paths, random seeds, and hyperparameter defaults
used across the entire pipeline (preprocessing, training, API).
"""

import os

# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

MODELS_DIR = os.path.join(BASE_DIR, "models", "saved")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

for _dir in (PROCESSED_DATA_DIR, MODELS_DIR, LOGS_DIR, DOCS_DIR):
    os.makedirs(_dir, exist_ok=True)

# ---------------------------------------------------------------------------
# Raw dataset file paths
# ---------------------------------------------------------------------------
RAW_PATHS = {
    "diabetes": os.path.join(RAW_DATA_DIR, "pima_diabetes.csv"),
    "heart": os.path.join(RAW_DATA_DIR, "cleveland_heart.csv"),
    "hypertension": os.path.join(RAW_DATA_DIR, "hypertension_risk.csv"),
}

# Processed (cleaned + scaled) dataset output paths
PROCESSED_PATHS = {
    "diabetes": os.path.join(PROCESSED_DATA_DIR, "diabetes_processed.csv"),
    "heart": os.path.join(PROCESSED_DATA_DIR, "heart_processed.csv"),
    "hypertension": os.path.join(PROCESSED_DATA_DIR, "hypertension_processed.csv"),
}

# Per-disease target column name
TARGET_COLUMN = {
    "diabetes": "Outcome",
    "heart": "target",
    "hypertension": "Hypertension",
}

# Per-disease raw column names (Pima dataset ships with no header row)
PIMA_COLUMNS = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
    "Outcome",
]

# Categorical columns that require label/one-hot encoding, per disease
CATEGORICAL_COLUMNS = {
    "diabetes": [],
    "heart": ["sex", "cp", "fbs", "restecg", "exang", "slope", "thal"],
    "hypertension": ["SmokingStatus"],
}

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Train/test split
# ---------------------------------------------------------------------------
TEST_SIZE = 0.2

# ---------------------------------------------------------------------------
# Feature selection
# ---------------------------------------------------------------------------
RFE_N_FEATURES_TO_SELECT = {
    "diabetes": 6,
    "heart": 8,
    "hypertension": 10,
}
CORRELATION_THRESHOLD = 0.9  # drop one of a pair of features above this |corr|

# ---------------------------------------------------------------------------
# Model hyperparameter search spaces (defaults; GridSearchCV explores these)
# ---------------------------------------------------------------------------
LOGISTIC_REGRESSION_PARAM_GRID = {
    "C": [0.1, 1, 10],
    "solver": ["liblinear", "lbfgs"],
    "max_iter": [1000],
}

RANDOM_FOREST_PARAM_GRID = {
    "n_estimators": [100, 200],
    "max_depth": [6, None],
    "min_samples_split": [2, 5],
}

ANN_CONFIG = {
    "hidden_units": [128, 64, 32],
    "dropout_rate": 0.3,
    "activation": "relu",
    "learning_rate": 1e-3,
    "batch_size": 32,
    "epochs": 60,
    "early_stopping_patience": 8,
}

ANN_TUNER_CONFIG = {
    "max_trials": 5,
    "executions_per_trial": 1,
    "epochs": 30,
}

CV_FOLDS = 10  # used for final model evaluation (evaluate.py)
GRID_SEARCH_CV_FOLDS = 5  # used inside GridSearchCV (lighter, for speed)
CONFIDENCE_THRESHOLD = 0.5

DISEASES = ["diabetes", "heart", "hypertension"]
