from combined_risk_engine import calculate_combined_risk


accident_probabilities = {
    "Fatal": 36.67,
    "Minor": 42.67,
    "Serious": 20.67
}

result = calculate_combined_risk(
    accident_probabilities=accident_probabilities,
    road_damage_score=40,
    landslide_score=20
)

print("\nCOMBINED RISK RESULT")
print("====================")

for key, value in result.items():
    print(f"{key}: {value}")