"""
NER-LogiAI Route Recommendation Engine
Phase 1 Production Release
"""


def _normalize_feature(values, val, default=50.0):
    """
    Scale a feature value relative to min and max values across candidate routes
    into a standard 0 to 100 scale.
    """
    valid_vals = [v for v in values if v is not None]
    if not valid_vals:
        return default
    min_v = min(valid_vals)
    max_v = max(valid_vals)
    if max_v == min_v:
        return default
    v_curr = val if val is not None else min_v
    return ((v_curr - min_v) / (max_v - min_v)) * 100.0


def get_weights(analysis_mode: str = "Balanced assessment"):
    mode_str = (analysis_mode or "").lower()
    if "risk" in mode_str:
        return 0.20, 0.70, 0.10  # Risk-first: 70% risk score, 20% time, 10% distance
    elif "time" in mode_str:
        return 0.60, 0.20, 0.20  # Time-first: 60% travel time, 20% risk score, 20% distance
    else:
        return 0.40, 0.40, 0.20  # Balanced: 40% travel time, 40% risk score, 20% distance


def calculate_route_scores(routes, analysis_mode: str = "Balanced assessment"):
    """
    Calculate normalized route scores for a collection of routes.
    Lower score = preferred route.
    """
    if not routes:
        return []

    w_time, w_risk, w_dist = get_weights(analysis_mode)

    times = [r.get("travel_time") or r.get("duration_minutes") for r in routes]
    distances = [r.get("distance") or r.get("distance_km") for r in routes]
    risks = [r.get("risk_score") for r in routes]

    scored_routes = []
    for route in routes:
        route_copy = route.copy()

        t_val = route_copy.get("travel_time") or route_copy.get("duration_minutes") or 0.0
        d_val = route_copy.get("distance") or route_copy.get("distance_km") or 0.0
        r_val = route_copy.get("risk_score")

        norm_time = _normalize_feature(times, t_val)
        norm_dist = _normalize_feature(distances, d_val)
        norm_risk = _normalize_feature(risks, r_val) if r_val is not None else 0.0

        score = (norm_time * w_time) + (norm_risk * w_risk) + (norm_dist * w_dist)
        route_score = round(score, 2)

        route_copy["route_score"] = route_score
        route_copy["calculated_score"] = route_score
        scored_routes.append(route_copy)

    return scored_routes


def recommend_route(routes, analysis_mode: str = "Balanced assessment"):
    """
    Compare available routes and recommend
    the route with the lowest weighted score.
    """
    if not routes:
        return {
            "status": "error",
            "message": "No routes available"
        }

    w_time, w_risk, w_dist = get_weights(analysis_mode)
    scored_routes = calculate_route_scores(routes, analysis_mode)

    def sort_key(r):
        s_score = r.get("route_score", 0.0)
        r_score = r.get("risk_score") if r.get("risk_score") is not None else 999.0
        t_time = r.get("travel_time") or r.get("duration_minutes") or 0.0
        d_dist = r.get("distance") or r.get("distance_km") or 0.0
        return (s_score, r_score, t_time, d_dist)

    recommended_route = min(scored_routes, key=sort_key)

    return {
        "status": "success",
        "recommended_route": recommended_route,
        "all_routes": scored_routes,
        "disclaimer": (
            f"Experimental normalized route scoring ({analysis_mode}). "
            f"Weighted: {int(w_time*100)}% travel time, {int(w_risk*100)}% risk score, {int(w_dist*100)}% distance."
        )
    }
