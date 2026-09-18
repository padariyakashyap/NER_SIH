"""
NER-LogiAI Route API
Hybrid routing:
- OpenRouteService (ORS) for shorter journeys
- OSRM public demo server for longer journeys and free fallback
"""

from pathlib import Path
import math
import os
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# =====================================================
# CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ORS_API_KEY = os.getenv("ORS_API_KEY")

ORS_BASE_URL = "https://api.heigit.org"
ORS_DIRECTIONS_URL = (
    f"{ORS_BASE_URL}/openrouteservice/v2/directions/driving-car/geojson"
)

OSRM_BASE_URL = "https://router.project-osrm.org"
OSRM_PROFILE = "driving"

# This is a straight-line distance threshold.
# Road distance can be longer than straight-line distance.
# Using 80 km gives a safety margin before the ORS alternatives limit.
ORS_DISTANCE_THRESHOLD_KM = 80.0


from fastapi.middleware.cors import CORSMiddleware

# =====================================================
# FASTAPI APPLICATION
# =====================================================

app = FastAPI(
    title="NER-LogiAI Route API",
    description=(
        "Hybrid route calculation using OpenRouteService and OSRM"
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# REQUEST MODELS
# =====================================================

class Coordinate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate

    # Number of alternative routes requested.
    # 0 means only one route.
    alternative_count: int = Field(
        default=2,
        ge=0,
        le=3,
    )
    analysis_mode: str = Field(
        default="Balanced assessment",
        description="Assessment mode: Balanced assessment, Risk-first assessment, or Time-first assessment"
    )


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def haversine_distance_km(
    origin: Coordinate,
    destination: Coordinate,
) -> float:
    """Calculate straight-line distance between two coordinates."""

    earth_radius_km = 6371.0

    lat1 = math.radians(origin.lat)
    lat2 = math.radians(destination.lat)

    delta_lat = math.radians(destination.lat - origin.lat)
    delta_lng = math.radians(destination.lng - origin.lng)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lng / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius_km * c


def build_coordinates(data: RouteRequest) -> List[List[float]]:
    """
    Routing services require coordinates in [longitude, latitude] format.
    """

    return [
        [data.origin.lng, data.origin.lat],
        [data.destination.lng, data.destination.lat],
    ]


def normalize_route(
    index: int,
    distance_meters: float,
    duration_seconds: float,
    geometry: Dict[str, Any],
    provider: str,
) -> Dict[str, Any]:
    """Convert ORS and OSRM responses into one common response format."""

    return {
        "route_id": f"route_{index + 1}",
        "provider": provider,
        "distance_meters": round(distance_meters, 2),
        "distance_km": round(distance_meters / 1000, 2),
        "duration_seconds": round(duration_seconds, 2),
        "duration_minutes": round(duration_seconds / 60, 2),
        "geometry": geometry or {},
        # Placeholder until the risk model is integrated.
        "risk_score": None,
    }


async def request_ors_routes(
    data: RouteRequest,
) -> List[Dict[str, Any]]:
    """Request routes from OpenRouteService."""

    if not ORS_API_KEY:
        raise RuntimeError("ORS_API_KEY is missing in .env")

    request_body: Dict[str, Any] = {
        "coordinates": build_coordinates(data),
        "instructions": False,
        "geometry": True,
    }

    # ORS alternative routes are added only when requested.
    if data.alternative_count > 0:
        request_body["alternative_routes"] = {
            "target_count": min(data.alternative_count + 1, 3),
            "share_factor": 0.8,
            "weight_factor": 1.4,
        }

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            ORS_DIRECTIONS_URL,
            json=request_body,
            headers=headers,
        )

    if response.status_code != 200:
        raise RuntimeError(
            "OpenRouteService request failed: "
            f"{response.status_code} - {response.text}"
        )

    result = response.json()
    features = result.get("features", [])

    routes: List[Dict[str, Any]] = []

    for index, feature in enumerate(features):
        properties = feature.get("properties", {})
        summary = properties.get("summary", {})

        distance_meters = summary.get("distance", 0)
        duration_seconds = summary.get("duration", 0)

        routes.append(
            normalize_route(
                index=index,
                distance_meters=distance_meters,
                duration_seconds=duration_seconds,
                geometry=feature.get("geometry", {}),
                provider="openrouteservice",
            )
        )

    if not routes:
        raise RuntimeError("OpenRouteService returned no routes")

    return routes


async def request_osrm_routes(
    data: RouteRequest,
) -> List[Dict[str, Any]]:
    """Request routes from the free OSRM public demo server."""

    coordinates = build_coordinates(data)

    # OSRM uses longitude,latitude;longitude,latitude.
    coordinate_string = ";".join(
        f"{longitude},{latitude}"
        for longitude, latitude in coordinates
    )

    url = (
        f"{OSRM_BASE_URL}/route/v1/{OSRM_PROFILE}/"
        f"{coordinate_string}"
    )

    # OSRM accepts a number for alternatives.
    # The server may return fewer alternatives or none.
    requested_alternatives = min(data.alternative_count, 2)

    params = {
        "alternatives": requested_alternatives,
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, params=params)

    if response.status_code != 200:
        raise RuntimeError(
            "OSRM request failed: "
            f"{response.status_code} - {response.text}"
        )

    result = response.json()

    if result.get("code") != "Ok":
        raise RuntimeError(
            f"OSRM returned an error: {result.get('message', result)}"
        )

    raw_routes = result.get("routes", [])

    if not raw_routes:
        raise RuntimeError("OSRM returned no routes")

    routes: List[Dict[str, Any]] = []

    for index, route_data in enumerate(raw_routes):
        routes.append(
            normalize_route(
                index=index,
                distance_meters=route_data.get("distance", 0),
                duration_seconds=route_data.get("duration", 0),
                geometry=route_data.get("geometry", {}),
                provider="osrm",
            )
        )

    return routes


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/")
def home():
    return {
        "status": "success",
        "message": "NER-LogiAI Route API is running",
        "service": "Hybrid ORS + OSRM",
        "ors_configured": bool(ORS_API_KEY),
        "osrm_available": True,
        "ors_distance_threshold_km": ORS_DISTANCE_THRESHOLD_KM,
    }


try:
    from ai_backend.risk_model.corridor_risk_engine import evaluate_corridor_risk
    from ai_backend.risk_model.route_optimizer import recommend_route
except ImportError:
    from risk_model.corridor_risk_engine import evaluate_corridor_risk
    from risk_model.route_optimizer import recommend_route


# =====================================================
# ROUTE CALCULATION
# =====================================================

@app.post("/calculate")
async def calculate_routes(data: RouteRequest):
    """
    Routing strategy:

    1. Estimate straight-line distance.
    2. Use OSRM for longer journeys because ORS alternatives
       have a distance limitation.
    3. Use ORS for shorter journeys when an API key is configured.
    4. Fall back to OSRM if ORS is unavailable or fails.
    5. Evaluate spatial corridor hazard scores (Landslide, Accident, Road Damage).
    6. Perform min-max relative scaling & generate route recommendation.
    """

    estimated_distance_km = haversine_distance_km(
        data.origin,
        data.destination,
    )

    use_osrm = (
        estimated_distance_km > ORS_DISTANCE_THRESHOLD_KM
        or not ORS_API_KEY
    )

    provider_used = "osrm"
    fallback_reason = None

    try:
        if use_osrm:
            raw_routes = await request_osrm_routes(data)
            provider_used = "osrm"

        else:
            try:
                raw_routes = await request_ors_routes(data)
                provider_used = "openrouteservice"

            except (httpx.RequestError, RuntimeError) as ors_error:
                # OSRM is used as a fallback if ORS fails.
                fallback_reason = str(ors_error)
                raw_routes = await request_osrm_routes(data)
                provider_used = "osrm_fallback"

    except httpx.RequestError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to connect to routing service: {str(error)}",
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        )

    # Evaluate spatial corridor risk for each route polyline
    enriched_routes = []
    for idx, route in enumerate(raw_routes):
        route_copy = route.copy()
        risk_eval = evaluate_corridor_risk(
            geometry=route_copy.get("geometry"),
            origin=data.origin.model_dump(),
            destination=data.destination.model_dump(),
            route_index=idx
        )
        route_copy["risk_score"] = risk_eval["overall_risk_score"]
        route_copy["risk_category"] = risk_eval["risk_category"]
        route_copy["component_scores"] = risk_eval["component_scores"]
        route_copy["weights"] = risk_eval["weights"]
        enriched_routes.append(route_copy)

    # Run normalized route recommendation engine
    opt_result = recommend_route(enriched_routes, data.analysis_mode)
    scored_routes = opt_result.get("all_routes", enriched_routes)
    recommended_route = opt_result.get("recommended_route", scored_routes[0])

    response: Dict[str, Any] = {
        "status": "success",
        "origin": data.origin.model_dump(),
        "destination": data.destination.model_dump(),
        "estimated_straight_line_distance_km": round(
            estimated_distance_km,
            2,
        ),
        "provider_used": provider_used,
        "route_count": len(scored_routes),
        "recommended_route": recommended_route,
        "routes": scored_routes,
        "disclaimer": opt_result.get("disclaimer", "Spatial corridor risk and normalized scoring evaluation.")
    }

    if fallback_reason:
        response["fallback_reason"] = fallback_reason

    return response

