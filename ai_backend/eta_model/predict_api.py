"""
ETA Prediction FastAPI Web Service

This module exposes a REST API around the ETA prediction model using FastAPI and Pydantic.
It imports `predict_eta` from `predict.py` to ensure prediction logic remains centralized.

Endpoints:
    - GET /             : Service welcome message
    - GET /health       : Service health check status
    - POST /predict-eta : Calculate predicted ETA for a bus GPS observation record
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

# Import prediction logic from predict module
try:
    from ai_backend.eta_model.predict import predict_eta
except ImportError:
    from predict import predict_eta


app = FastAPI(
    title="ETA Prediction API",
    description="Machine Learning REST API for public transit bus ETA prediction.",
    version="1.0.0"
)


class ETARequest(BaseModel):
    """Pydantic request schema for ETA prediction input."""
    bus_id: int = Field(..., description="Bus identifier")
    route_id: int = Field(..., description="Route identifier")
    latitude: float = Field(..., description="Current bus latitude coordinate")
    longitude: float = Field(..., description="Current bus longitude coordinate")
    current_speed: float = Field(..., description="Current bus speed in km/h")
    historical_avg_speed: float = Field(..., description="Historical average speed for route & time slot")
    historical_delay_minutes: float = Field(..., description="Historical delay in minutes")
    time_slot: int = Field(..., ge=0, le=23, description="Time slot hour (0-23)")
    nearest_stop_index: int = Field(..., ge=0, description="Nearest route stop index")
    destination_stop_index: int = Field(..., ge=0, description="Destination stop index")
    distance_to_destination_km: float = Field(..., ge=0.0, description="Distance to destination stop in km")
    effective_speed: float = Field(..., gt=0.0, description="Effective blended speed in km/h")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bus_id": 0,
                "route_id": 0,
                "latitude": 22.58656076490561,
                "longitude": 88.32355563485277,
                "current_speed": 38.0,
                "historical_avg_speed": 40.0,
                "historical_delay_minutes": 4.498095607205338,
                "time_slot": 6,
                "nearest_stop_index": 1,
                "destination_stop_index": 2,
                "distance_to_destination_km": 7.932459579115933,
                "effective_speed": 39.0
            }
        }
    )


class ETAResponse(BaseModel):
    """Pydantic response schema for ETA prediction output."""
    success: bool
    eta_minutes: float


@app.get("/")
def read_root():
    """Root endpoint identifying the ETA prediction API."""
    return {
        "message": "ETA Prediction API is running",
        "service": "eta_prediction",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "eta_prediction"
    }


@app.post("/predict-eta", response_model=ETAResponse)
def predict_eta_endpoint(request: ETARequest):
    """
    Predict bus ETA in minutes based on current position, route, speed, and historical metrics.
    """
    try:
        input_data = request.model_dump()
        eta_result = predict_eta(input_data)
        return {
            "success": True,
            "eta_minutes": float(eta_result)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ETA prediction failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
