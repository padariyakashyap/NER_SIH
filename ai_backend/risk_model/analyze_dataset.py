from pathlib import Path
import pandas as pd

# File path
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "accident_prediction_india.csv"

# Load dataset
df = pd.read_csv(DATA_PATH)

print("=== DATASET ANALYSIS ===")

print("\n1. Dataset Shape:")
print(df.shape)

print("\n2. Missing Values:")
print(df.isnull().sum())

print("\n3. Severity Distribution:")
print(df["Accident Severity"].value_counts())

print("\n4. Data Types:")
print(df.dtypes)

print("\n5. Numerical Statistics:")
print(df.describe().to_string())

print("\n6. Unique Values:")
for column in df.columns:
    print(f"{column}: {df[column].nunique()} unique values")

print("\n7. Severity vs Fatalities:")
print(pd.crosstab(
    df["Number of Fatalities"],
    df["Accident Severity"],
    normalize="index"
).round(2))

print("\n8. Severity vs Casualties:")
print(pd.crosstab(
    df["Number of Casualties"],
    df["Accident Severity"],
    normalize="index"
).round(2))