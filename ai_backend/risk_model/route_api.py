from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List

from ai_backend.risk_model.route_optimizer import recommend_route


app = FastAPI(
    title="NER-LogiAI Route Recommendation API",
    description="Experimental route scoring for Phase 1 MVP",
    version="1.0"
)


class Route(BaseModel):
    route_name: str
    distance: float = Field(ge=0)
    travel_time: float = Field(ge=0)
    risk_score: float = Field(ge=0, le=100)


class RouteRequest(BaseModel):
    routes: List[Route]


@app.get("/")
def home():
    return {
        "message": "NER-LogiAI Route API is running"
    }


@app.post("/recommend-route")
def recommend_route_api(request: RouteRequest):
    routes = [
        route.model_dump()
        for route in request.routes
    ]

    return recommend_route(routes)