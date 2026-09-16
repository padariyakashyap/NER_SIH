"""
ETA Model Independent Evaluation Script

This script loads the pre-trained model artifact (`eta_model.joblib`) and feature schema
(`feature_columns.json`), performs robust validation and sanity checks, evaluates the model on
the 20% test split, compares its metrics against a naive mean-baseline predictor, and displays
detailed evaluation metrics alongside sample predictions.
"""

import json
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import max_error, mean_absolute_error, mean_squared_error, median_absolute_error, r2_score
from sklearn.model_selection import train_test_split

# Define file paths using pathlib relative to this script file
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

dataset_path = DATA_DIR / "eta_training_data.csv"
model_path = BASE_DIR / "eta_model.joblib"
feature_columns_path = BASE_DIR / "feature_columns.json"


def run_sanity_checks():
    """Verify that all required files, features, and non-null values are present."""
    print("Performing initial sanity checks...")

    if not model_path.exists():
        raise FileNotFoundError(f"Sanity Check Failed: Model file missing at {model_path}")

    if not feature_columns_path.exists():
        raise FileNotFoundError(f"Sanity Check Failed: Feature columns file missing at {feature_columns_path}")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Sanity Check Failed: Dataset file missing at {dataset_path}")

    # Load dataset & feature list
    df = pd.read_csv(dataset_path)
    with open(feature_columns_path, "r", encoding="utf-8") as f:
        feature_cols = json.load(f)

    target_col = "eta_minutes"

    # Check for missing feature columns in dataset
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Sanity Check Failed: Missing required feature columns in dataset: {missing_cols}")

    if target_col not in df.columns:
        raise KeyError(f"Sanity Check Failed: Target column '{target_col}' missing from dataset.")

    # Check for missing/null values
    null_counts = df[feature_cols + [target_col]].isnull().sum()
    total_nulls = null_counts.sum()
    if total_nulls > 0:
        raise ValueError(f"Sanity Check Failed: Found {total_nulls} missing values in target or features:\n{null_counts[null_counts > 0]}")

    print("All sanity checks passed successfully.\n")
    return df, feature_cols, target_col


def main():
    try:
        df, feature_cols, target_col = run_sanity_checks()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # 1. Load model artifact
    model = joblib.load(model_path)

    # 2. Extract features and target
    X = df[feature_cols]
    y = df[target_col]

    # 3. Create 80/20 train/test split with random_state=42
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    # 4. Evaluate Random Forest model on test set
    y_pred_rf = model.predict(X_test)

    rf_mae = mean_absolute_error(y_test, y_pred_rf)
    rf_rmse = np.sqrt(mean_squared_error(y_test, y_pred_rf))
    rf_r2 = r2_score(y_test, y_pred_rf)
    rf_max_err = max_error(y_test, y_pred_rf)
    rf_median_err = median_absolute_error(y_test, y_pred_rf)

    # 5. Baseline Prediction (Mean ETA from training set)
    baseline_mean_eta = y_train.mean()
    y_pred_baseline = np.full_like(y_test, fill_value=baseline_mean_eta)

    baseline_mae = mean_absolute_error(y_test, y_pred_baseline)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, y_pred_baseline))
    baseline_r2 = r2_score(y_test, y_pred_baseline)

    # 6. Display evaluation statistics
    print("=" * 70)
    print("ETA MODEL INDEPENDENT EVALUATION REPORT")
    print("=" * 70)
    print(f"Dataset File:       {dataset_path}")
    print(f"Model File:         {model_path}")
    print(f"Test Samples:       {len(X_test)}")
    print(f"Feature Columns ({len(feature_cols)}): {feature_cols}")

    print("\n" + "-" * 70)
    print("RANDOM FOREST MODEL PERFORMANCE")
    print("-" * 70)
    print(f"Mean Absolute Error (MAE):     {rf_mae:.4f} minutes")
    print(f"Root Mean Squared Error (RMSE): {rf_rmse:.4f} minutes")
    print(f"R² Score:                      {rf_r2:.4f}")
    print(f"Median Absolute Error:         {rf_median_err:.4f} minutes")
    print(f"Maximum Absolute Error:        {rf_max_err:.4f} minutes")

    print("\n" + "-" * 70)
    print("NAIVE MEAN BASELINE COMPARISON")
    print("-" * 70)
    print(f"Baseline (Training Mean ETA): {baseline_mean_eta:.4f} minutes")
    print(f"Baseline MAE:                  {baseline_mae:.4f} minutes")
    print(f"Baseline RMSE:                 {baseline_rmse:.4f} minutes")
    print(f"Baseline R² Score:             {baseline_r2:.4f}")

    print("\n" + "-" * 70)
    print("IMPROVEMENT OVER BASELINE")
    print("-" * 70)
    mae_improvement = ((baseline_mae - rf_mae) / baseline_mae) * 100
    rmse_improvement = ((baseline_rmse - rf_rmse) / baseline_rmse) * 100
    print(f"MAE Reduction:  {mae_improvement:.2f}% improvement")
    print(f"RMSE Reduction: {rmse_improvement:.2f}% improvement")

    # 7. Print 10 test predictions
    print("\n" + "=" * 70)
    print("10 TEST SAMPLE PREDICTIONS (ACTUAL vs PREDICTED)")
    print("=" * 70)

    sample_df = pd.DataFrame({
        "Actual ETA (min)": y_test.iloc[:10].values,
        "Predicted ETA (min)": y_pred_rf[:10],
        "Abs Error (min)": np.abs(y_test.iloc[:10].values - y_pred_rf[:10])
    })
    print(sample_df.to_string(index=False))

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
