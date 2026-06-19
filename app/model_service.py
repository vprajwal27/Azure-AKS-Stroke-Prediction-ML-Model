"""Loads the trained pipeline once and exposes a simple predict function."""

from pathlib import Path

import joblib
import pandas as pd

from app.schemas import PatientFeatures, PredictionResponse

ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "at_risk_lgbm_model.joblib"

# Column order the pipeline was trained on. We rebuild this explicitly
# rather than trusting dict ordering from the request body.
FEATURE_COLUMNS = [
    "age",
    "gender",
    "chest_pain",
    "high_blood_pressure",
    "irregular_heartbeat",
    "shortness_of_breath",
    "fatigue_weakness",
    "dizziness",
    "swelling_edema",
    "neck_jaw_pain",
    "excessive_sweating",
    "persistent_cough",
    "nausea_vomiting",
    "chest_discomfort",
    "cold_hands_feet",
    "snoring_sleep_apnea",
    "anxiety_doom",
]


class ModelService:
    """Thin wrapper so the FastAPI app never touches sklearn/joblib directly."""

    def __init__(self, artifact_path: Path = ARTIFACT_PATH):
        self._artifact_path = artifact_path
        self._pipeline = None

    def load(self) -> None:
        self._pipeline = joblib.load(self._artifact_path)

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None

    def predict(self, features: PatientFeatures) -> PredictionResponse:
        if self._pipeline is None:
            raise RuntimeError("Model is not loaded yet.")

        row = pd.DataFrame([features.model_dump()], columns=FEATURE_COLUMNS)
        probability = float(self._pipeline.predict_proba(row)[0, 1])
        label = "at_risk" if probability >= 0.5 else "not_at_risk"
        return PredictionResponse(prediction=label, probability=probability)


# Single shared instance, populated during the app's startup lifespan hook.
model_service = ModelService()
