# ML-Powered Early Disease Prediction System

A production-ready, end-to-end machine learning system for chronic disease risk prediction — covering **Diabetes**, **Cardiovascular Disease**, and **Hypertension** — with model explainability via SHAP, a Flask REST API, and a React 18 frontend.

---

## Architecture

```
disease-prediction/
├── data/
│   ├── raw/                        # Source datasets (downloaded/generated)
│   └── processed/                  # Cleaned, scaled, feature-selected CSVs
├── models/saved/                   # Trained .joblib and .h5 model files + scalers
├── src/
│   ├── utils/
│   │   ├── config.py               # All paths, seeds, hyperparameter defaults
│   │   └── logger.py               # Rotating file + console logger
│   ├── preprocessing/
│   │   ├── clean_data.py           # Load, impute, encode, scale
│   │   ├── feature_selection.py    # Correlation filter + RFE
│   │   ├── dataset.py              # SMOTE + tf.data pipeline
│   │   └── run_pipeline.py         # Main preprocessing entry point
│   ├── models/
│   │   ├── logistic_regression.py  # LR + GridSearchCV
│   │   ├── random_forest.py        # RF + GridSearchCV
│   │   ├── ann.py                  # 3-layer MLP + KerasTuner
│   │   ├── evaluate.py             # Metrics, ROC curves, 10-fold CV
│   │   └── compare_models.py       # Trains all models, exports report
│   ├── explainability/
│   │   └── shap_explainer.py       # TreeExplainer / LinearExplainer / KernelExplainer
│   └── api/
│       ├── app.py                  # Flask factory with CORS
│       ├── database.py             # SQLAlchemy + prediction_logs table
│       ├── schemas.py              # Pydantic input validation
│       ├── utils.py                # Model/scaler caching + build_model_input
│       └── routes/
│           ├── predict.py          # POST /predict
│           └── explain.py          # POST /explain/<disease>
├── frontend/
│   └── src/
│       ├── services/api.js         # Axios client
│       ├── components/
│       │   ├── PatientForm.jsx     # Full patient input form
│       │   ├── PredictionResult.jsx # Per-disease risk cards with gauges
│       │   └── ShapChart.jsx       # SHAP horizontal bar chart (Recharts)
│       └── App.jsx
├── tests/
│   ├── test_preprocessing.py
│   ├── test_models.py
│   └── test_api.py
├── docs/
│   ├── api_documentation.yaml      # OpenAPI 3.0 spec
│   └── model_comparison_report.md  # Auto-generated after training
├── docker-compose.yml
└── README.md
```

---

## Datasets

| Disease | Dataset | Source | Size |
|---|---|---|---|
| Diabetes | Pima Indians Diabetes | [Brønlee ML Datasets](https://github.com/jbrownlee/Datasets) | 768 rows |
| Heart Disease | Cleveland Heart Disease | [UCI / sharmaroshan](https://github.com/sharmaroshan/Heart-UCI-Dataset) | 303 rows |
| Hypertension | Synthetic risk dataset | Generated via `data/raw/generate_hypertension_data.py` | 1200 rows |

> **Note on hypertension data:** No canonical public hypertension-risk dataset with the required features (lifestyle, biometrics, family history) exists at the scale of the Pima/Cleveland datasets. The synthetic dataset uses a medically-plausible logistic risk function with realistic feature distributions and ~32% prevalence. In a production clinical deployment, this should be replaced with real EHR data.

---

## Prerequisites

- Python 3.10+ (tested on 3.12)
- Node.js 18+ and npm 9+
- PostgreSQL (optional; SQLite is used by default)

---

## Local Setup

### 1. Clone and install Python dependencies

```bash
git clone <repo-url>
cd disease-prediction

pip install flask flask-cors pydantic sqlalchemy psycopg2-binary \
            scikit-learn imbalanced-learn shap joblib pandas numpy \
            matplotlib tensorflow-cpu keras-tuner tensorboard tabulate
```

### 2. Download datasets

```bash
# Pima Diabetes
curl -o data/raw/pima_diabetes.csv \
  https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv

# Cleveland Heart Disease
curl -o data/raw/cleveland_heart.csv \
  https://raw.githubusercontent.com/sharmaroshan/Heart-UCI-Dataset/master/heart.csv

# Synthetic Hypertension (generate locally)
python3 data/raw/generate_hypertension_data.py
```

### 3. Run the full ML pipeline

```bash
# Step 1: Preprocess all datasets
python3 -m src.preprocessing.run_pipeline

# Step 2: Train + compare all models (Logistic Regression, Random Forest, ANN)
# This generates docs/model_comparison_report.md and saves models to models/saved/
python3 -m src.models.compare_models
```

### 4. Start the Flask API

```bash
python3 -m src.api.app
# API running at http://localhost:5000
```

To use PostgreSQL instead of SQLite, set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/disease_prediction"
python3 -m src.api.app
```

### 5. Start the React frontend

```bash
cd frontend
cp .env.example .env
npm install
npm start
# Frontend running at http://localhost:3000
```

---

## Running Tests

### Python (pytest)

```bash
# From the project root:
python3 -m pytest tests/ -v
```

All 27 tests should pass. The `test_models` and `test_api` suites require the
trained models to exist; run step 3 above before running them.

### React (Jest / React Testing Library)

```bash
cd frontend
npm test
```

---

## Running with Docker

```bash
docker-compose up --build
```

Services:
- **PostgreSQL** on port 5432
- **Flask API** on port 5000 (waits for Postgres to be healthy before starting)
- **React frontend** (optional; uncomment the `frontend` service in `docker-compose.yml`)

---

## API Endpoints

See `docs/api_documentation.yaml` for the full OpenAPI 3.0 spec.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/predict` | Run all three models for requested diseases |
| `POST` | `/explain/<disease>` | Get SHAP explanation for a disease prediction |

### Quick cURL example

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "patient": {
      "age": 45, "bmi": 28.4, "glucose": 130, "blood_pressure": 80,
      "cholesterol": 210, "family_history": 1, "smoking_status": "Former",
      "pregnancies": 2, "skin_thickness": 25, "insulin": 85,
      "diabetes_pedigree_function": 0.45, "sex": 1, "cp": 2,
      "fbs": 0, "restecg": 1, "thalach": 150, "exang": 0,
      "oldpeak": 1.2, "slope": 1, "ca": 0, "thal": 2,
      "sodium_intake": 3200, "alcohol_units_week": 4,
      "physical_activity_min_week": 90, "stress_score": 6,
      "resting_heart_rate": 76
    }
  }'
```

---

## Model Performance

After running `python3 -m src.models.compare_models`, see
`docs/model_comparison_report.md` for per-disease accuracy, AUC-ROC, and
10-fold CV results.

**Observed accuracy ranges (typical):**

| Disease | Logistic Regression | Random Forest | ANN |
|---|---|---|---|
| Diabetes | ~77–80% | ~80–84% | ~78–82% |
| Heart Disease | ~83–86% | ~85–88% | ~83–86% |
| Hypertension | ~75–82% | ~80–85% | ~76–83% |

> The 85% accuracy target is met for most model/disease combinations on heart disease and partially on the others. The Pima Diabetes dataset (~768 rows) and our synthetic hypertension data are modest in size — accuracy approaches 85%+ as training set size grows. In a clinical deployment, richer feature sets and larger cohorts would be expected to push all models above this threshold.

---

## Explainability

SHAP explanations are available for all three model types:

- **Random Forest** → `shap.TreeExplainer` (exact, fast)
- **Logistic Regression** → `shap.LinearExplainer` (operates in log-odds space, converted to probability)
- **ANN** → `shap.KernelExplainer` with 50-sample background (model-agnostic, slower)

The `/explain/<disease>` endpoint returns feature contributions sorted by
absolute SHAP magnitude, rendered as a horizontal bar chart in the frontend.
Red bars increase predicted risk; green bars decrease it.

---

## Disclaimer

This system is for educational and demonstration purposes only. It is not a
substitute for professional medical advice, diagnosis, or treatment. Risk
probabilities are statistical estimates based on population-level data and
should never be used as the sole basis for clinical decisions.
