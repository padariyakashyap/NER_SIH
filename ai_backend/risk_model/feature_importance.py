from pathlib import Path
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "risk_model.pkl"

# Load trained model
pipeline = joblib.load(MODEL_PATH)

# Get preprocessing and model
preprocessor = pipeline.named_steps["preprocessor"]
model = pipeline.named_steps["model"]

# Get transformed feature names
feature_names = preprocessor.get_feature_names_out()

# Get feature importance
importance = model.feature_importances_

# Create DataFrame
importance_df = pd.DataFrame({
    "Feature": feature_names,
    "Importance": importance
})

# Sort by importance
importance_df = importance_df.sort_values(
    by="Importance",
    ascending=False
)

print("\nTOP 20 IMPORTANT FEATURES:\n")
print(importance_df.head(20).to_string(index=False))