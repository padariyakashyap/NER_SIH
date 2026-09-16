from pathlib import Path
import joblib
import pandas as pd

from fastapi import FastAPI
from pydantic import BaseModel

# Paths
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "risk_model.pkl"

# Load model
model = joblib.load(MODEL_PATH)

app = FastAPI(title="NER-LogiAI Risk Prediction API")


class AccidentData(BaseModel):
    state_name: str
    city_name: str
    year: int
    month: str
    day_of_week: str
    time_of_day: str
    number_of_vehicles_involved: int
    vehicle_type_involved: str
    weather_conditions: str
    road_type: str
    road_condition: str
    lighting_conditions: str
    traffic_control_presence: str
    speed_limit: int
    driver_age: int
    driver_gender: str
    driver_license_status: str
    alcohol_involvement: str


@app.get("/")
def home():
    return {"message": "Risk Prediction API is running"}


@app.post("/predict-risk")
def predict_risk(data: AccidentData):

    input_data = pd.DataFrame([{
        "State Name": data.state_name,
        "City Name": data.city_name,
        "Year": data.year,
        "Month": data.month,
        "Day of Week": data.day_of_week,
        "Time of Day": data.time_of_day,
        "Number of Vehicles Involved": data.number_of_vehicles_involved,
        "Vehicle Type Involved": data.vehicle_type_involved,
        "Weather Conditions": data.weather_conditions,
        "Road Type": data.road_type,
        "Road Condition": data.road_condition,
        "Lighting Conditions": data.lighting_conditions,
        "Traffic Control Presence": data.traffic_control_presence,
        "Speed Limit (km/h)": data.speed_limit,
        "Driver Age": data.driver_age,
        "Driver Gender": data.driver_gender,
        "Driver License Status": data.driver_license_status,
        "Alcohol Involvement": data.alcohol_involvement
    }])

    prediction = model.predict(input_data)[0]
    probabilities = model.predict_proba(input_data)[0]

    classes = model.classes_

    probability_result = {
        str(cls): round(float(prob) * 100, 2)
        for cls, prob in zip(classes, probabilities)
    }

    return {
        "predicted_risk": prediction,
        "probabilities": probability_result,
        "disclaimer": "Experimental accident-severity prediction, not a verified route-risk score."
    }