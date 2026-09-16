"""
Baseline ETA Prediction Model Training Script

This script loads the preprocessed ETA dataset (`eta_training_data.csv`), prepares the features
and target (`eta_minutes`), splits the data into training (80%) and testing (20%) sets, trains
a RandomForestRegressor baseline model, evaluates model performance (MAE, RMSE, R²), prints
sample prediction results, and saves both the model artifact (`eta_model.joblib`) and feature 
schema (`feature_columns.json`).
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

# Define file paths using pathlib relative to this script
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

dataset_path = DATA_DIR / "eta_training_data.csv"
model_output_path = BASE_DIR / "eta_model.joblib"
feature_columns_output_path = BASE_DIR / "feature_columns.json"


def main():
    # 1. Load dataset
    print("Loading training dataset...")
    df = pd.read_csv(dataset_path)

    # 2. Define target and features
    target_col = "eta_minutes"
    
    # Explicit list of features to use for model training
    feature_cols = [
        "bus_id",
        "route_id",
        "latitude",
        "longitude",
        "current_speed",
        "historical_avg_speed",
        "historical_delay_minutes",
        "time_slot",
        "nearest_stop_index",
        "destination_stop_index",
        "distance_to_destination_km",
        "effective_speed",
    ]

    # Ensure all feature columns exist in dataset
    available_feature_cols = [col for col in feature_cols if col in df.columns]

    X = df[available_feature_cols]
    y = df[target_col]

    # 3. Train/Test Split (80% train, 20% test, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    # 4. Train baseline RandomForestRegressor
    print("Training RandomForestRegressor model...")
    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # 5. Model Evaluation
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # 6. Print summary metrics
    print("\n" + "=" * 60)
    print("ETA MODEL TRAINING RESULTS")
    print("=" * 60)
    print(f"Training samples: {len(X_train)}")
    print(f"Test samples:     {len(X_test)}")
    print(f"Features used ({len(available_feature_cols)}): {available_feature_cols}")
    print("-" * 60)
    print(f"Mean Absolute Error (MAE): {mae:.4f} minutes")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f} minutes")
    print(f"R² Score:                  {r2:.4f}")

    # 7. Print actual vs predicted table for 10 test samples
    print("\n" + "=" * 60)
    print("10 TEST SAMPLE PREDICTIONS (ACTUAL vs PREDICTED)")
    print("=" * 60)
    
    sample_df = pd.DataFrame({
        "Actual ETA (min)": y_test.iloc[:10].values,
        "Predicted ETA (min)": y_pred[:10],
        "Abs Error (min)": np.abs(y_test.iloc[:10].values - y_pred[:10])
    })
    print(sample_df.to_string(index=False))

    # 8. Save model and feature columns
    # Create parent directories if needed
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, model_output_path)
    print(f"\nModel successfully saved to: {model_output_path}")

    with open(feature_columns_output_path, "w", encoding="utf-8") as f:
        json.dump(available_feature_cols, f, indent=4)
    print(f"Feature columns saved to:    {feature_columns_output_path}")

    print("=" * 60)
    print("TRAINING PROCESS COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
