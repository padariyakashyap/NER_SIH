# Public Transit Bus ETA Prediction Module

This module provides an end-to-end Machine Learning pipeline and REST API for predicting bus Estimated Time of Arrival (ETA) in minutes for the SIH project.

---

## 1. Overview

The ETA Prediction module calculates estimated transit times for buses along defined routes using:
- Real-time GPS positional telemetry (latitude, longitude, speed)
- Route stop sequences and stop coordinates
- Historical time-slot averages (historical speed and historical delay minutes)

It includes data preprocessing scripts, a Random Forest baseline model, independent evaluation tools, a reusable Python inference function, and a FastAPI web service.

---

## 2. Dataset Structure

Dataset files are located under `ai_backend/eta_model/data/`:

| File Name | Description | Rows | Primary Columns |
| :--- | :--- | :--- | :--- |
| **`bus_gps_data.csv`** | Synthetic real-time bus telemetry stream | 2,000 | `bus_id`, `route_id`, `latitude`, `longitude`, `timestamp`, `speed` |
| **`historical_data.csv`** | Route performance by hour (0–23) | 120 | `route_id`, `time_slot`, `avg_speed`, `avg_delay_minutes` |
| **`route_data.csv`** | Ordered list of stops per route | 25 | `route_id`, `stop_name`, `latitude`, `longitude` |
| **`eta_training_data.csv`** | Processed feature store with target ETA | 2,000 | All features + derived `eta_minutes` target |

---

## 3. Proxy ETA Target Methodology

Because the raw synthetic dataset does not contain ground-truth arrival timestamps, a **proxy target (`eta_minutes`)** was derived systematically during dataset compilation (`build_dataset.py`):

1. **Nearest & Next Stop Identification:**
   For each GPS coordinate, the nearest stop on the route is matched (`nearest_stop_index`). The target destination is set to the subsequent stop (`destination_stop_index = min(nearest + 1, final)`).
2. **Geographic Distance:**
   Great-circle distance (`distance_to_destination_km`) between current GPS coordinates and destination stop coordinates is calculated using the **Haversine formula**.
3. **Effective Speed:**
   Current GPS speed and historical hourly average speed are blended:
   $$\text{effective\_speed} = \frac{\text{current\_speed} + \text{historical\_avg\_speed}}{2}$$
4. **Proxy ETA Formula:**
   $$\text{travel\_time\_minutes} = \left( \frac{\text{distance\_to\_destination\_km}}{\text{effective\_speed}} \right) \times 60$$
   $$\text{eta\_minutes} = \text{travel\_time\_minutes} + \text{historical\_delay\_minutes}$$

---

## 4. Model Architecture & Parameters

- **Algorithm:** `RandomForestRegressor` (`scikit-learn`)
- **Trees (`n_estimators`):** `200`
- **Split Ratio:** 80% Training (1,600 samples), 20% Testing (400 samples)
- **Random State:** `42` (reproducible)
- **Feature Set (12 Features):**
  - `bus_id`, `route_id`, `latitude`, `longitude`, `current_speed`, `historical_avg_speed`, `historical_delay_minutes`, `time_slot`, `nearest_stop_index`, `destination_stop_index`, `distance_to_destination_km`, `effective_speed`

---

## 5. Model Performance & Evaluation

> [!IMPORTANT]
> **Synthetic Target Notice:** The evaluation metrics below reflect performance on the synthetic proxy target. They demonstrate high mathematical consistency of the Random Forest regressor on the derived proxy formula, but **must NOT be interpreted as real-world traffic prediction accuracy**.

Evaluated on the 20% independent test split (`evaluate.py`):

- **Mean Absolute Error (MAE):** `0.1956 minutes` (~11.7 seconds)
- **Root Mean Squared Error (RMSE):** `0.2768 minutes`
- **$R^2$ Score:** `0.9961`
- **Median Absolute Error:** `0.1323 minutes`
- **Maximum Absolute Error:** `1.2941 minutes`

*Comparison vs Naive Baseline (Mean ETA = 14.16 min):* MAE is reduced by **94.54%** over baseline.

---

## 6. Local Python Integration

Other Python backend modules can import `predict_eta` directly from `predict.py`:

```python
from ai_backend.eta_model.predict import predict_eta

sample_record = {
    "bus_id": 0,
    "route_id": 0,
    "latitude": 22.58656076490561,
    "longitude": 88.32355563485277,
    "current_speed": 38.0,
    "historical_avg_speed": 40.0,
    "historical_delay_minutes": 4.498095607205338,
    "time_slot": 6,
    "nearest_stop_index": 1,
    "destination_stop_index": 2,
    "distance_to_destination_km": 7.932459579115933,
    "effective_speed": 39.0
}

predicted_eta = predict_eta(sample_record)
print(f"Predicted ETA: {predicted_eta:.2f} minutes")
```

---

## 7. FastAPI Service & API Endpoints

### Starting the Server
Start the Uvicorn web server locally:

```bash
python ai_backend\eta_model\predict_api.py
```
The server will run at `http://127.0.0.1:8000`. OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

### API Endpoints

#### 1. `GET /`
- **Description:** Root welcome message
- **Response:**
  ```json
  {
    "message": "ETA Prediction API is running",
    "service": "eta_prediction",
    "docs": "/docs"
  }
  ```

#### 2. `GET /health`
- **Description:** Health status check
- **Response:**
  ```json
  {
    "status": "ok",
    "service": "eta_prediction"
  }
  ```

#### 3. `POST /predict-eta`
- **Description:** Predict ETA in minutes for a single bus GPS payload
- **Headers:** `Content-Type: application/json`
- **Request Body Example:**
  ```json
  {
    "bus_id": 0,
    "route_id": 0,
    "latitude": 22.58656076490561,
    "longitude": 88.32355563485277,
    "current_speed": 38.0,
    "historical_avg_speed": 40.0,
    "historical_delay_minutes": 4.498095607205338,
    "time_slot": 6,
    "nearest_stop_index": 1,
    "destination_stop_index": 2,
    "distance_to_destination_km": 7.932459579115933,
    "effective_speed": 39.0
  }
  ```
- **Response Format:**
  ```json
  {
    "success": true,
    "eta_minutes": 16.597489926653168
  }
  ```

---

## 8. Current Limitations & Production Recommendations

1. **Synthetic Data:** The dataset is generated synthetically for development and testing.
2. **Proxy Target:** Model targets a calculated proxy formula rather than true arrival timestamps.
3. **No External Live Traffic:** Live traffic congestion maps, signals, or external routing APIs (e.g. Google Maps, OSRM) are not currently integrated.
4. **No Weather or Incidents:** Weather conditions, road construction, and vehicle breakdown events are not accounted for.
5. **Production Deployment:** For production use, the model must be retrained on actual real-world transit telemetry logs (`train.py`) containing true arrival times.
