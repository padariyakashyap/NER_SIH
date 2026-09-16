"""
ETA Reusable Inference Module

This module provides a clean, reusable function `predict_eta(input_data)` to load 
the pre-trained model artifact (`eta_model.joblib`) and feature columns schema 
(`feature_columns.json`) and calculate ETA predictions for a single input record.

Usage:
    from predict import predict_eta

    sample = {
        "bus_id": 0,
        "route_id": 0,
        "latitude": 22.58656076,
        "longitude": 88.32355563,
        "current_speed": 38,
        "historical_avg_speed": 40,
        "historical_delay_minutes": 4.4980956,
        "time_slot": 6,
        "nearest_stop_index": 1,
        "destination_stop_index": 2,
        "distance_to_destination_km": 7.93245958,
        "effective_speed": 39.0
    }
    eta = predict_eta(sample)
"""

import json
from pathlib import Path
import joblib
import pandas as pd

# Define paths relative to this file using pathlib
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "eta_model.joblib"
FEATURE_COLUMNS_PATH = BASE_DIR / "feature_columns.json"

# Cached global variables for lazy/singleton loading
_MODEL = None
_FEATURE_COLUMNS = None


def load_artifacts():
    """
    Load and cache model artifact and feature column configuration.
    Raises FileNotFoundError if files are missing.
    """
    global _MODEL, _FEATURE_COLUMNS

    if _MODEL is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")
        _MODEL = joblib.load(MODEL_PATH)

    if _FEATURE_COLUMNS is None:
        if not FEATURE_COLUMNS_PATH.exists():
            raise FileNotFoundError(f"Feature columns schema file not found at: {FEATURE_COLUMNS_PATH}")
        with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
            _FEATURE_COLUMNS = json.load(f)

    return _MODEL, _FEATURE_COLUMNS


def predict_eta(input_data: dict) -> float:
    """
    Predict Estimated Time of Arrival (ETA) in minutes for a single record dictionary.

    Parameters
    ----------
    input_data : dict
        Dictionary containing all required feature keys.

    Returns
    -------
    float
        Predicted ETA in minutes (non-negative).
    """
    if not isinstance(input_data, dict):
        raise TypeError(f"Expected input_data to be a dict, got {type(input_data).__name__}")

    model, feature_columns = load_artifacts()

    # 1. Validate all required features are present
    missing_features = [col for col in feature_columns if col not in input_data]
    if missing_features:
        raise KeyError(f"Missing required feature(s) in input_data: {missing_features}")

    # 2. Validate feature value data types (must be numeric int or float)
    row_data = {}
    for col in feature_columns:
        val = input_data[col]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise ValueError(f"Invalid non-numeric value for feature '{col}': {val} (type: {type(val).__name__})")
        row_data[col] = float(val)

    # 3. Construct DataFrame with exact feature ordering
    df_input = pd.DataFrame([row_data], columns=feature_columns)

    # 4. Predict ETA
    pred_raw = model.predict(df_input)[0]
    predicted_eta = float(pred_raw)

    # 5. Ensure non-negative output
    if predicted_eta < 0.0:
        predicted_eta = 0.0

    return predicted_eta


if __name__ == "__main__":
    print("=" * 60)
    print("ETA PREDICTION TEST")
    print("=" * 60)

    # Realistic sample chosen directly from row 2 of eta_training_data.csv
    sample_input = {
        "bus_id": 0,
        "route_id": 0,
        "latitude": 22.58656076490561,
        "longitude": 88.32355563485277,
        "current_speed": 38,
        "historical_avg_speed": 40,
        "historical_delay_minutes": 4.498095607205338,
        "time_slot": 6,
        "nearest_stop_index": 1,
        "destination_stop_index": 2,
        "distance_to_destination_km": 7.932459579115933,
        "effective_speed": 39.0
    }

    print("\nInput:")
    print(json.dumps(sample_input, indent=4))

    eta = predict_eta(sample_input)

    print("\nPredicted ETA:")
    print(f"{eta:.4f} minutes")
    print("=" * 60)
