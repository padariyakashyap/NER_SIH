from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List

from ai_backend.risk_model.combined_risk_engine import (
    calculate_combined_risk
)

from ai_backend.risk_model.route_optimizer import (
    recommend_route
)


app = FastAPI(
    title="NER-LogiAI Unified Route Analysis API",
    description="Combined risk and route recommendation for Phase 1 MVP",
    version="1.0"
)


class Route(BaseModel):
    route_name: str
    distance: float = Field(ge=0)
    travel_time: float = Field(ge=0)
    risk_score: float = Field(ge=0, le=100)


class RouteAnalysisRequest(BaseModel):
    accident_probabilities: dict[str, float]
    road_damage_score: float = Field(default=0.0, ge=0, le=100)
    landslide_score: float = Field(default=0.0, ge=0, le=100)
    routes: List[Route]


@app.get("/")
def home():
    return {
        "message": "NER-LogiAI Unified Route Analysis API is running"
    }


@app.post("/analyze-route")
def analyze_route(request: RouteAnalysisRequest):

    # Calculate combined risk
    risk_result = calculate_combined_risk(
        accident_probabilities=request.accident_probabilities,
        road_damage_score=request.road_damage_score,
        landslide_score=request.landslide_score
    )

    # Recommend the best-scoring route
    routes = [
        route.model_dump()
        for route in request.routes
    ]

    route_result = recommend_route(routes)

    return {
        "status": "success",
        "risk_analysis": risk_result,
        "route_recommendation": route_result,
        "disclaimer": (
            "Experimental prototype. "
            "Risk scores are not validated probabilities "
            "of route failure."
        )
    }