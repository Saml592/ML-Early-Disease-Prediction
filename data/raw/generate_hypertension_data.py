"""
generate_hypertension_data.py
------------------------------
There is no single canonical public "Hypertension Risk" dataset analogous to
Pima Diabetes or Cleveland Heart Disease. This script generates a synthetic
but medically-plausible dataset using well-documented hypertension risk
factors (age, BMI, sodium intake, smoking, family history, physical
activity, stress, alcohol use) with realistic correlations and a logistic
risk function plus noise, so model training/evaluation is meaningful.

The resulting CSV is saved to data/raw/hypertension_risk.csv and is treated
as a stand-in for a real clinical dataset. This limitation is documented in
the README.
"""

import numpy as np
import pandas as pd
import os

RNG = np.random.default_rng(42)
N = 1200


def generate():
    age = RNG.normal(48, 15, N).clip(18, 90)
    bmi = RNG.normal(27, 5, N).clip(15, 55)
    sodium_intake = RNG.normal(3400, 900, N).clip(800, 7000)  # mg/day
    smoking_status = RNG.choice(
        ["Never", "Former", "Current"], size=N, p=[0.55, 0.25, 0.20]
    )
    alcohol_units_week = RNG.gamma(2.0, 3.0, N).clip(0, 40)
    physical_activity_min_week = RNG.normal(120, 90, N).clip(0, 600)
    family_history = RNG.choice([0, 1], size=N, p=[0.6, 0.4])
    stress_score = RNG.normal(5, 2, N).clip(0, 10)  # self-reported 0-10
    resting_heart_rate = RNG.normal(72, 10, N).clip(45, 130)
    cholesterol = RNG.normal(195, 35, N).clip(100, 400)
    glucose = RNG.normal(100, 25, N).clip(60, 300)

    smoke_map = {"Never": 0.0, "Former": 0.4, "Current": 1.0}
    smoke_num = np.array([smoke_map[s] for s in smoking_status])

    def z_score(arr):
        return (arr - arr.mean()) / arr.std()

    # Logistic risk function combining STANDARDIZED risk factors so no
    # single raw-scale feature dominates the log-odds.
    z = (
        -1.35
        + 0.55 * z_score(age)
        + 0.45 * z_score(bmi)
        + 0.35 * z_score(sodium_intake)
        + 0.70 * smoke_num
        + 0.25 * z_score(alcohol_units_week)
        - 0.30 * z_score(physical_activity_min_week)
        + 0.60 * family_history
        + 0.30 * z_score(stress_score)
        + 0.15 * z_score(resting_heart_rate)
        + 0.20 * z_score(cholesterol)
        + 0.25 * z_score(glucose)
        + RNG.normal(0, 0.45, N)
    )
    prob = 1 / (1 + np.exp(-z))
    target = (RNG.uniform(0, 1, N) < prob).astype(int)

    df = pd.DataFrame(
        {
            "Age": age.round(0).astype(int),
            "BMI": bmi.round(1),
            "SodiumIntake": sodium_intake.round(0).astype(int),
            "SmokingStatus": smoking_status,
            "AlcoholUnitsWeek": alcohol_units_week.round(1),
            "PhysicalActivityMinWeek": physical_activity_min_week.round(0).astype(int),
            "FamilyHistory": family_history,
            "StressScore": stress_score.round(1),
            "RestingHeartRate": resting_heart_rate.round(0).astype(int),
            "Cholesterol": cholesterol.round(0).astype(int),
            "Glucose": glucose.round(0).astype(int),
            "Hypertension": target,
        }
    )
    # Introduce a few missing values to exercise imputation logic
    for col in ["BMI", "Cholesterol", "Glucose"]:
        mask = RNG.uniform(0, 1, N) < 0.03
        df.loc[mask, col] = np.nan

    return df


if __name__ == "__main__":
    data = generate()
    output_path = os.path.join(os.path.dirname(__file__), "hypertension_risk.csv")
    data.to_csv(output_path, index=False)
    print(f"Saved {len(data)} rows. Positive rate: {data['Hypertension'].mean():.2%}")
