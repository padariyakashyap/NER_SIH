"""
NER-LogiAI Spatial Corridor Risk Mapping Engine
Phase 1 Production Release

Evaluates spatial geometry coordinates [lng, lat] and corridor endpoints
against regional Northeast India hazard models:
- Landslide Terrain Exposure Model
- Highway Accident Frequency Model
- Pavement Condition Index
"""

import math
from typing import Any, Dict, List, Optional, Tuple


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance in kilometers between two lat/lng coordinates."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def _extract_points(geometry: Any) -> List[Tuple[float, float]]:
    """Extract (lat, lng) tuples from GeoJSON or raw coordinate lists."""
    points: List[Tuple[float, float]] = []
    if not geometry:
        return points

    raw_list: List[Any] = []
    if isinstance(geometry, list):
        raw_list = geometry
    elif isinstance(geometry, dict) and "coordinates" in geometry:
        raw_list = geometry["coordinates"]

    for item in raw_list:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            val0, val1 = float(item[0]), float(item[1])
            # GeoJSON coordinates are [longitude, latitude]
            if abs(val0) <= 180 and abs(val1) <= 90:
                if abs(val0) > abs(val1) and abs(val0) > 40:
                    points.append((val1, val0))
                else:
                    points.append((val0, val1))
    return points


# Regional spatial hazard profiles for Northeast India transport corridors
CORRIDOR_HAZARD_ZONES = [
    # Shillong / Meghalaya Plateau (High Landslide & Rainfall Slope Risk)
    {"center_lat": 25.5788, "center_lng": 91.8933, "radius_km": 60.0, "landslide_base": 58.0, "accident_base": 38.0, "damage_base": 42.0},
    # Jowai / NH-6 Freight Corridor (Very High Slope Exposure & Road Damage)
    {"center_lat": 25.4500, "center_lng": 92.2000, "radius_km": 50.0, "landslide_base": 68.0, "accident_base": 42.0, "damage_base": 55.0},
    # Kohima / Nagaland Winding Corridor
    {"center_lat": 25.6751, "center_lng": 94.1086, "radius_km": 45.0, "landslide_base": 62.0, "accident_base": 45.0, "damage_base": 48.0},
    # Imphal / Manipur Transport Ring
    {"center_lat": 24.8170, "center_lng": 93.9368, "radius_km": 45.0, "landslide_base": 48.0, "accident_base": 40.0, "damage_base": 50.0},
    # Guwahati / Urban Highway Interchange (Higher Accident Frequency)
    {"center_lat": 26.1445, "center_lng": 91.7362, "radius_km": 35.0, "landslide_base": 18.0, "accident_base": 52.0, "damage_base": 28.0},
    # Dibrugarh / Upper Assam Corridor
    {"center_lat": 27.4728, "center_lng": 94.9120, "radius_km": 40.0, "landslide_base": 22.0, "accident_base": 35.0, "damage_base": 32.0},
    # Gangtok / Sikkim Himalayan Corridor
    {"center_lat": 27.3389, "center_lng": 88.6065, "radius_km": 50.0, "landslide_base": 72.0, "accident_base": 36.0, "damage_base": 45.0},
    # Aizawl / Mizoram Hill Section
    {"center_lat": 23.7271, "center_lng": 92.7176, "radius_km": 45.0, "landslide_base": 60.0, "accident_base": 39.0, "damage_base": 44.0}
]


def evaluate_corridor_risk(
    geometry: Any = None,
    origin: Optional[Dict[str, float]] = None,
    destination: Optional[Dict[str, float]] = None,
    route_index: int = 0
) -> Dict[str, Any]:
    """
    Evaluate segment-based spatial hazard exposure for a route polyline.

    Returns:
    - overall_risk_score: float (0 - 100)
    - risk_category: "Low" | "Medium" | "High"
    - component_scores: { accident: float, road_damage: float, landslide: float }
    - weights: { accident: 0.40, road_damage: 0.30, landslide: 0.30 }
    """
    points = _extract_points(geometry)
    if not points and origin and destination:
        points = [(origin["lat"], origin["lng"]), (destination["lat"], destination["lng"])]

    if not points:
        # Default baseline if no geometry or endpoints supplied
        landslide_score = 25.0
        accident_score = 30.0
        damage_score = 28.0
    else:
        # Sample points along the route geometry
        sample_step = max(1, len(points) // 25)
        sampled_points = points[::sample_step]

        landslide_accum = 0.0
        accident_accum = 0.0
        damage_accum = 0.0

        for lat, lng in sampled_points:
            pt_landslide = 20.0  # Default plains baseline
            pt_accident = 28.0
            pt_damage = 25.0

            for zone in CORRIDOR_HAZARD_ZONES:
                dist = _haversine_km(lat, lng, zone["center_lat"], zone["center_lng"])
                if dist <= zone["radius_km"]:
                    proximity_factor = 1.0 - (dist / zone["radius_km"])
                    pt_landslide = max(pt_landslide, zone["landslide_base"] * (0.6 + 0.4 * proximity_factor))
                    pt_accident = max(pt_accident, zone["accident_base"] * (0.7 + 0.3 * proximity_factor))
                    pt_damage = max(pt_damage, zone["damage_base"] * (0.7 + 0.3 * proximity_factor))

            landslide_accum += pt_landslide
            accident_accum += pt_accident
            damage_accum += pt_damage

        n_samples = len(sampled_points)
        landslide_score = round(landslide_accum / n_samples, 2)
        accident_score = round(accident_accum / n_samples, 2)
        damage_score = round(damage_accum / n_samples, 2)

    # Clamp individual components
    landslide_score = max(0.0, min(100.0, landslide_score))
    accident_score = max(0.0, min(100.0, accident_score))
    damage_score = max(0.0, min(100.0, damage_score))

    # Calculate overall weighted risk score
    # Weights: 40% Accident, 30% Road Damage, 30% Landslide
    overall_score = round(
        (accident_score * 0.40) + (damage_score * 0.30) + (landslide_score * 0.30),
        2
    )
    overall_score = max(0.0, min(100.0, overall_score))

    if overall_score < 35.0:
        category = "Low"
    elif overall_score < 65.0:
        category = "Medium"
    else:
        category = "High"

    return {
        "overall_risk_score": overall_score,
        "risk_category": category,
        "component_scores": {
            "accident": accident_score,
            "road_damage": damage_score,
            "landslide": landslide_score
        },
        "weights": {
            "accident": 0.40,
            "road_damage": 0.30,
            "landslide": 0.30
        },
        "disclaimer": (
            "Spatial corridor hazard evaluation based on Northeast India terrain, "
            "highway accident density, and pavement condition signals."
        )
    }
