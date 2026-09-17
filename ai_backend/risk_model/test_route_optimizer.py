from route_optimizer import recommend_route


routes = [
    {
        "route_name": "Route A",
        "distance": 120,
        "travel_time": 180,
        "risk_score": 40
    },
    {
        "route_name": "Route B",
        "distance": 140,
        "travel_time": 200,
        "risk_score": 25
    },
    {
        "route_name": "Route C",
        "distance": 100,
        "travel_time": 160,
        "risk_score": 70
    }
]


result = recommend_route(routes)


print("\nROUTE RECOMMENDATION")
print("====================")

print("Status:", result["status"])

print(
    "Recommended Route:",
    result["recommended_route"]["route_name"]
)

print(
    "Route Score:",
    result["recommended_route"]["route_score"]
)

print("\nAll Routes:")

for route in result["all_routes"]:
    print(
        route["route_name"],
        "→ Score:",
        route["route_score"]
    )