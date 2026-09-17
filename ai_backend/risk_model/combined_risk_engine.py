from typing import Dict


def calculate_accident_risk(
    probabilities: Dict[str, float]
) -> float:
    """
    Convert accident severity probabilities into
    an experimental risk score from 0 to 100.
    """

    severity_weights = {
        "Minor": 30,
        "Serious": 65,
        "Fatal": 100
    }

    risk_score = 0.0

    for severity, probability in probabilities.items():
        weight = severity_weights.get(severity, 0)
        risk_score += (probability / 100) * weight

    return round(risk_score, 2)


def calculate_combined_risk(
    accident_probabilities: Dict[str, float],
    road_damage_score: float = 0.0,
    landslide_score: float = 0.0
) -> Dict:

    accident_risk = calculate_accident_risk(
        accident_probabilities
    )

    # Experimental weighted combination
    combined_score = (
        accident_risk * 0.40
        + road_damage_score * 0.30
        + landslide_score * 0.30
    )

    combined_score = round(
        max(0.0, min(100.0, combined_score)), 2
    )

    if combined_score < 35:
        category = "Low"
    elif combined_score < 65:
        category = "Medium"
    else:
        category = "High"

    return {
        "overall_risk_score": combined_score,
        "risk_category": category,
        "component_scores": {
            "accident_risk": accident_risk,
            "road_damage_risk": road_damage_score,
            "landslide_risk": landslide_score
        },
        "weights": {
            "accident": 0.40,
            "road_damage": 0.30,
            "landslide": 0.30
        },
        "disclaimer": (
            "Experimental weighted risk score. "
            "Not a validated probability of route failure."
        )
    }