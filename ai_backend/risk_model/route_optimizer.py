"""
NER-LogiAI Route Recommendation Engine
Phase 1 MVP
"""


def calculate_route_score(route):
    """
    Lower score = better route.

    We consider:
    - Travel time: 40%
    - Risk score: 40%
    - Distance: 20%
    """

    travel_time = route["travel_time"]
    risk_score = route["risk_score"]
    distance = route["distance"]

    score = (
        travel_time * 0.40
        + risk_score * 0.40
        + distance * 0.20
    )

    return round(score, 2)


def recommend_route(routes):
    """
    Compare available routes and recommend
    the route with the lowest weighted score.
    """

    if not routes:
        return {
            "status": "error",
            "message": "No routes available"
        }

    scored_routes = []

    for route in routes:
        route_copy = route.copy()

        route_copy["route_score"] = calculate_route_score(
            route
        )

        scored_routes.append(route_copy)

    recommended_route = min(
        scored_routes,
        key=lambda route: (
            route["route_score"],
            route["risk_score"],
            route["travel_time"],
            route["distance"]
        )
    )

    return {
        "status": "success",
        "recommended_route": recommended_route,
        "all_routes": scored_routes,
        "disclaimer": (
            "Experimental route scoring. "
            "Not a guaranteed optimal route."
        )
    }