from pathlib import Path
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score


# 1. Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "accident_prediction_india.csv"
MODEL_PATH = BASE_DIR / "risk_model.pkl"


# 2. Load dataset
print("Loading dataset...")
df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)


# 3. Remove columns that could cause data leakage
drop_columns = [
    "Accident Severity",
    "Number of Casualties",
    "Number of Fatalities",
    "Accident Location Details"
]

X = df.drop(columns=drop_columns)
y = df["Accident Severity"]


# 4. Identify feature types
categorical_features = X.select_dtypes(
    include=["object"]
).columns.tolist()

numerical_features = X.select_dtypes(
    exclude=["object"]
).columns.tolist()


# 5. Preprocessing
numerical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median"))
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False
    ))
])


preprocessor = ColumnTransformer([
    ("numerical", numerical_pipeline, numerical_features),
    ("categorical", categorical_pipeline, categorical_features)
])


# 6. Machine Learning model
model = RandomForestClassifier(
    n_estimators=150,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)


pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", model)
])


# 7. Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# 8. Train model
print("Training risk model...")
pipeline.fit(X_train, y_train)


# 9. Evaluate model
predictions = pipeline.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\nModel Accuracy:", round(accuracy, 4))
print("\nClassification Report:")
print(classification_report(y_test, predictions))


# 10. Save trained model
joblib.dump(pipeline, MODEL_PATH)

print("\nModel saved successfully at:")
print(MODEL_PATH)