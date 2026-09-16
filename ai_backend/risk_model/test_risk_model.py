from pathlib import Path
import pandas as pd
import joblib


# File paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "accident_prediction_india.csv"
MODEL_PATH = BASE_DIR / "risk_model.pkl"


# Load model and dataset
print("Loading model...")
model = joblib.load(MODEL_PATH)

df = pd.read_csv(DATA_PATH)


# Prepare sample input
drop_columns = [
    "Accident Severity",
    "Number of Casualties",
    "Number of Fatalities",
    "Accident Location Details"
]

X = df.drop(columns=drop_columns)

# Select one accident record
sample = X.iloc[[0]]


# Make prediction
prediction = model.predict(sample)[0]
probabilities = model.predict_proba(sample)[0]
classes = model.classes_


# Display results
print("\n--- Risk Prediction Result ---")
print("Predicted Severity:", prediction)

print("\nPrediction Probabilities:")
for class_name, probability in zip(classes, probabilities):
    print(f"{class_name}: {probability:.2%}")