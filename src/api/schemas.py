"""
schemas.py
----------
Pydantic models for validating incoming patient data. A single
`PatientData` model covers the union of raw fields needed across all three
diseases (diabetes, heart disease, hypertension); most fields are optional
since a given prediction request only needs the subset relevant to the
disease(s) being scored. `utils.py` enforces per-disease required-field
checks at preprocessing time and returns a clear error if a needed field
is missing.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class PatientData(BaseModel):
    """Union schema of all raw clinical/lifestyle fields used by the three
    disease-risk models. Field names are normalized to snake_case; see
    `src/api/utils.py::FEATURE_NAME_MAP` for the mapping back to each
    dataset's original (model-facing) column names."""

    # --- Shared / common ---
    age: int = Field(..., ge=1, le=120, description="Patient age in years")
    bmi: Optional[float] = Field(None, ge=10, le=80, description="Body Mass Index")
    glucose: Optional[float] = Field(
        None, ge=0, le=500, description="Blood glucose (mg/dL)"
    )
    blood_pressure: Optional[float] = Field(
        None, ge=0, le=300, description="Resting blood pressure / diastolic-ish (mm Hg)"
    )
    cholesterol: Optional[float] = Field(
        None, ge=0, le=700, description="Serum cholesterol (mg/dL)"
    )
    family_history: Optional[Literal[0, 1]] = Field(
        None, description="1 if immediate family history of the condition, else 0"
    )
    smoking_status: Optional[Literal["Never", "Former", "Current"]] = Field(
        None, description="Smoking status"
    )

    # --- Diabetes-specific (Pima) ---
    pregnancies: Optional[int] = Field(
        None, ge=0, le=20, description="Number of pregnancies"
    )
    skin_thickness: Optional[float] = Field(
        None, ge=0, le=100, description="Triceps skinfold thickness (mm)"
    )
    insulin: Optional[float] = Field(
        None, ge=0, le=900, description="2-Hour serum insulin (mu U/ml)"
    )
    diabetes_pedigree_function: Optional[float] = Field(
        None, ge=0, le=3, description="Diabetes pedigree function score"
    )

    # --- Heart disease-specific (Cleveland) ---
    sex: Optional[Literal[0, 1]] = Field(None, description="0 = female, 1 = male")
    cp: Optional[Literal[0, 1, 2, 3]] = Field(None, description="Chest pain type (0-3)")
    fbs: Optional[Literal[0, 1]] = Field(
        None, description="Fasting blood sugar > 120 mg/dl (1 = true)"
    )
    restecg: Optional[Literal[0, 1, 2]] = Field(
        None, description="Resting ECG results (0-2)"
    )
    thalach: Optional[float] = Field(
        None, ge=0, le=250, description="Max heart rate achieved during exercise"
    )
    exang: Optional[Literal[0, 1]] = Field(
        None, description="Exercise-induced angina (1 = yes)"
    )
    oldpeak: Optional[float] = Field(
        None, ge=0, le=10, description="ST depression induced by exercise"
    )
    slope: Optional[Literal[0, 1, 2]] = Field(
        None, description="Slope of peak exercise ST segment"
    )
    ca: Optional[Literal[0, 1, 2, 3, 4]] = Field(
        None, description="Number of major vessels colored by fluoroscopy"
    )
    thal: Optional[Literal[0, 1, 2, 3]] = Field(None, description="Thalassemia type")

    # --- Hypertension-specific ---
    sodium_intake: Optional[float] = Field(
        None, ge=0, le=10000, description="Sodium intake (mg/day)"
    )
    alcohol_units_week: Optional[float] = Field(
        None, ge=0, le=100, description="Alcohol units consumed per week"
    )
    physical_activity_min_week: Optional[float] = Field(
        None, ge=0, le=1500, description="Minutes of physical activity per week"
    )
    stress_score: Optional[float] = Field(
        None, ge=0, le=10, description="Self-reported stress score (0-10)"
    )
    resting_heart_rate: Optional[float] = Field(
        None, ge=30, le=220, description="Resting heart rate (bpm)"
    )

    @field_validator("smoking_status")
    @classmethod
    def normalize_smoking_status(cls, v):
        if v is None:
            return v
        return v.strip().capitalize()

    model_config = {
        "json_schema_extra": {
            "example": {
                "age": 45,
                "bmi": 28.4,
                "glucose": 130,
                "blood_pressure": 80,
                "cholesterol": 210,
                "family_history": 1,
                "smoking_status": "Former",
                "pregnancies": 2,
                "skin_thickness": 25,
                "insulin": 85,
                "diabetes_pedigree_function": 0.45,
                "sex": 1,
                "cp": 2,
                "fbs": 0,
                "restecg": 1,
                "thalach": 150,
                "exang": 0,
                "oldpeak": 1.2,
                "slope": 1,
                "ca": 0,
                "thal": 2,
                "sodium_intake": 3200,
                "alcohol_units_week": 4,
                "physical_activity_min_week": 90,
                "stress_score": 6,
                "resting_heart_rate": 76,
            }
        }
    }


class PredictionRequest(BaseModel):
    """Wraps a PatientData payload; `diseases` optionally restricts which
    disease models to run (defaults to all three)."""

    patient: PatientData
    diseases: Optional[list[Literal["diabetes", "heart", "hypertension"]]] = None


class ExplainRequest(BaseModel):
    """Payload for the /explain/<disease> endpoint."""

    patient: PatientData
