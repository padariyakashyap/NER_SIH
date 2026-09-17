"""
ETA Prediction FastAPI Web Service

This module exposes a REST API around the ETA prediction model using FastAPI and Pydantic.
It imports `predict_eta` from `predict.py` to ensure prediction logic remains centralized.

Endpoints:
    - GET /                     : Service welcome message
    - GET /health               : Service health check status
    - POST /predict-eta         : Calculate predicted ETA from pre-calculated 12 features
    - POST /predict-eta-raw     : Calculate predicted ETA directly from raw GPS telemetry
"""

from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

# Import prediction logic from predict module
try:
    from ai_backend.eta_model.predict import predict_eta
except ImportError:
    from predict import predict_eta

# File paths using pathlib relative to this module
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ROUTE_DATA_PATH = DATA_DIR / "route_data.csv"
HISTORICAL_DATA_PATH = DATA_DIR / "historical_data.csv"

# Cached DataFrames for raw GPS feature lookup
_ROUTE_DF = None
_HISTORICAL_DF = None


def load_data_tables():
    """Load and cache route and historical CSV datasets."""
    global _ROUTE_DF, _HISTORICAL_DF
    if _ROUTE_DF is None:
        if not ROUTE_DATA_PATH.exists():
            raise FileNotFoundError(f"Route dataset file missing at: {ROUTE_DATA_PATH}")
        _ROUTE_DF = pd.read_csv(ROUTE_DATA_PATH)
    if _HISTORICAL_DF is None:
        if not HISTORICAL_DATA_PATH.exists():
            raise FileNotFoundError(f"Historical dataset file missing at: {HISTORICAL_DATA_PATH}")
        _HISTORICAL_DF = pd.read_csv(HISTORICAL_DATA_PATH)
    return _ROUTE_DF, _HISTORICAL_DF


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth specified in decimal degrees using the Haversine formula.
    """
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371.0  # Earth's radius in kilometers
    return r * c


app = FastAPI(
    title="ETA Prediction API",
    description="Machine Learning REST API for public transit bus ETA prediction.",
    version="1.0.0"
)


class ETARequest(BaseModel):
    """Pydantic request schema for pre-processed feature input."""
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


class RawGPSRequest(BaseModel):
    """Pydantic request schema for raw GPS telemetry input."""
    bus_id: int = Field(..., description="Bus identifier")
    route_id: int = Field(..., description="Route identifier")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Current bus latitude coordinate (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Current bus longitude coordinate (-180 to 180)")
    speed: float = Field(..., ge=0.0, description="Current bus speed in km/h (>= 0)")
    timestamp: datetime = Field(..., description="GPS observation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bus_id": 0,
                "route_id": 0,
                "latitude": 22.58656076490561,
                "longitude": 88.32355563485277,
                "speed": 38.0,
                "timestamp": "2024-01-01T06:00:00"
            }
        }
    )


class RawGPSResponse(BaseModel):
    """Pydantic response schema for raw GPS prediction output."""
    success: bool
    eta_minutes: float
    bus_id: int
    route_id: int
    nearest_stop_index: int
    destination_stop_index: int
    distance_to_destination_km: float


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
    Predict bus ETA in minutes based on pre-processed feature dictionary.
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


@app.post("/predict-eta-raw", response_model=RawGPSResponse)
def predict_eta_raw_endpoint(request: RawGPSRequest):
    """
    Predict bus ETA in minutes directly from raw GPS telemetry input.
    Derives nearest stop index, destination stop, Haversine distance, and historical metrics automatically.
    """
    try:
        route_df, historical_df = load_data_tables()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database lookup failed: {str(e)}"
        )

    # 1. Filter route stops for requested route_id
    route_stops = route_df[route_df["route_id"] == request.route_id].reset_index(drop=True)
    if route_stops.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Route ID {request.route_id} not found in route database."
        )

    # 2. Extract timestamp hour for time_slot (0-23)
    time_slot = request.timestamp.hour

    # 3. Calculate Haversine distance from bus position to all stops on this route
    stop_lats = route_stops["latitude"].values
    stop_lons = route_stops["longitude"].values
    dist_to_all_stops = haversine(request.latitude, request.longitude, stop_lats, stop_lons)

    nearest_stop_index = int(np.argmin(dist_to_all_stops))
    final_stop_index = len(route_stops) - 1
    destination_stop_index = min(nearest_stop_index + 1, final_stop_index)

    # 4. Target destination stop coordinates & distance
    dest_lat = float(route_stops.loc[destination_stop_index, "latitude"])
    dest_lon = float(route_stops.loc[destination_stop_index, "longitude"])
    distance_to_destination_km = float(haversine(request.latitude, request.longitude, dest_lat, dest_lon))

    # 5. Filter historical statistics for matching (route_id, time_slot)
    hist_match = historical_df[
        (historical_df["route_id"] == request.route_id) &
        (historical_df["time_slot"] == time_slot)
    ]
    if hist_match.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Historical metrics not found for route_id {request.route_id} and time_slot {time_slot}."
        )

    hist_row = hist_match.iloc[0]
    historical_avg_speed = float(hist_row["avg_speed"])
    historical_delay_minutes = float(hist_row["avg_delay_minutes"])

    # 6. Effective speed computation
    effective_speed = float((request.speed + historical_avg_speed) / 2.0)

    # 7. Construct 12 model features dictionary
    features_dict = {
        "bus_id": request.bus_id,
        "route_id": request.route_id,
        "latitude": request.latitude,
        "longitude": request.longitude,
        "current_speed": request.speed,
        "historical_avg_speed": historical_avg_speed,
        "historical_delay_minutes": historical_delay_minutes,
        "time_slot": time_slot,
        "nearest_stop_index": nearest_stop_index,
        "destination_stop_index": destination_stop_index,
        "distance_to_destination_km": distance_to_destination_km,
        "effective_speed": effective_speed,
    }

    # 8. Invoke ETA prediction model
    try:
        eta_result = predict_eta(features_dict)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ETA model execution failed: {str(e)}"
        )

    return {
        "success": True,
        "eta_minutes": float(eta_result),
        "bus_id": request.bus_id,
        "route_id": request.route_id,
        "nearest_stop_index": nearest_stop_index,
        "destination_stop_index": destination_stop_index,
        "distance_to_destination_km": distance_to_destination_km,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
