from pathlib import Path
import sys

from fastapi import FastAPI
from pydantic import BaseModel, Field

# Allow importing the engine from this directory
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from combined_risk_engine import calculate_combined_risk


app = FastAPI(
    title="NER-LogiAI Combined Risk API",
    description="Experimental multi-factor risk assessment engine"
)


class CombinedRiskRequest(BaseModel):
    accident_probabilities: dict[str, float]
    road_damage_score: float = Field(default=0.0, ge=0, le=100)
    landslide_score: float = Field(default=0.0, ge=0, le=100)


@app.get("/")
def home():
    return {
        "message": "Combined Risk API is running"
    }


@app.post("/combined-risk")
def combined_risk(data: CombinedRiskRequest):

    result = calculate_combined_risk(
        accident_probabilities=data.accident_probabilities,
        road_damage_score=data.road_damage_score,
        landslide_score=data.landslide_score
    )

    return result