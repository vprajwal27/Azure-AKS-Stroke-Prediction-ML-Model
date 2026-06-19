"""Request/response models for the at_risk prediction API."""

from typing import Literal

from pydantic import BaseModel, Field

BinaryFlag = Literal[0, 1]


class PatientFeatures(BaseModel):
    """Raw patient inputs. Field names/types mirror the training data exactly."""

    age: int = Field(..., ge=0, le=120, description="Age in years")
    gender: Literal["Male", "Female"]
    chest_pain: BinaryFlag
    high_blood_pressure: BinaryFlag
    irregular_heartbeat: BinaryFlag
    shortness_of_breath: BinaryFlag
    fatigue_weakness: BinaryFlag
    dizziness: BinaryFlag
    swelling_edema: BinaryFlag
    neck_jaw_pain: BinaryFlag
    excessive_sweating: BinaryFlag
    persistent_cough: BinaryFlag
    nausea_vomiting: BinaryFlag
    chest_discomfort: BinaryFlag
    cold_hands_feet: BinaryFlag
    snoring_sleep_apnea: BinaryFlag
    anxiety_doom: BinaryFlag

    model_config = {
        "json_schema_extra": {
            "example": {
                "age": 67,
                "gender": "Male",
                "chest_pain": 1,
                "high_blood_pressure": 1,
                "irregular_heartbeat": 1,
                "shortness_of_breath": 1,
                "fatigue_weakness": 1,
                "dizziness": 0,
                "swelling_edema": 0,
                "neck_jaw_pain": 0,
                "excessive_sweating": 1,
                "persistent_cough": 0,
                "nausea_vomiting": 0,
                "chest_discomfort": 1,
                "cold_hands_feet": 0,
                "snoring_sleep_apnea": 1,
                "anxiety_doom": 0,
            }
        }
    }


class PredictionResponse(BaseModel):
    prediction: Literal["at_risk", "not_at_risk"]
    probability: float = Field(..., ge=0.0, le=1.0, description="P(at_risk), 0-1")


class HealthResponse(BaseModel):
    status: Literal["ok", "unavailable"]
    model_loaded: bool
