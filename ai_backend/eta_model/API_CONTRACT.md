# Public Transit ETA Prediction API Contract

This document defines the REST API contract for integrating the **ETA Prediction Module** into external backend systems and web/mobile frontend applications.

---

## 1. Overview & Purpose

The ETA Prediction API provides real-time Estimated Time of Arrival (ETA) predictions in minutes for public transit buses along specified routes. It accepts bus positional telemetry, route stop progress, current speed, and historical route performance metrics to return an estimated arrival duration.

---

## 2. Server Configuration

- **Unified Gateway Base URL:** `http://127.0.0.1:8000`
- **Standalone ETA Base URL:** `http://127.0.0.1:8000/api/eta`
- **Content-Type:** `application/json`

---

## 3. Endpoints Specification

### Endpoint 1: Predict Bus ETA

- **Path:** `POST /api/eta/predict-eta`
- **Description:** Accepts bus positional data and historical route metrics, returns the predicted ETA in minutes.
- **Request Format:** `JSON`
- **Response Format:** `JSON`

#### Required Request Fields (12 Fields)

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `bus_id` | `integer` | Unique bus vehicle identifier |
| `route_id` | `integer` | Unique transit route identifier |
| `latitude` | `float` | Current bus latitude coordinate (decimal degrees) |
| `longitude` | `float` | Current bus longitude coordinate (decimal degrees) |
| `current_speed` | `float` | Current GPS speed of the bus (km/h) |
| `historical_avg_speed` | `float` | Historical average speed for route & hour slot (km/h) |
| `historical_delay_minutes` | `float` | Historical average delay for route & hour slot (minutes) |
| `time_slot` | `integer` | Current hour of day (`0` to `23`) |
| `nearest_stop_index` | `integer` | Sequence index of nearest route stop (`0`, `1`, `2`, ...) |
| `destination_stop_index` | `integer` | Sequence index of targeted destination stop |
| `distance_to_destination_km` | `float` | Distance from bus position to destination stop (km) |
| `effective_speed` | `float` | Blended effective speed: `(current_speed + historical_avg_speed) / 2` (km/h) |

#### Example Request Payload

```json
{
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
```

#### Successful Response Payload (`HTTP 200 OK`)

```json
{
  "success": true,
  "eta_minutes": 16.597489926653168
}
```

---

### Endpoint 2: Health Check

- **Path:** `GET /api/eta/health`
- **Description:** Verifies that the ETA service sub-application is active and operational.

#### Successful Response Payload (`HTTP 200 OK`)

```json
{
  "status": "ok",
  "service": "eta_prediction"
}
```

---

## 4. Integration Code Examples

### A. Python Backend Integration (`requests`)

```python
import requests

url = "http://127.0.0.1:8000/api/eta/predict-eta"
payload = {
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

response = requests.post(url, json=payload)
data = response.json()

if data.get("success"):
    print(f"Predicted ETA: {data['eta_minutes']:.2f} minutes")
```

### B. JavaScript Frontend Integration (`fetch`)

```javascript
async function getBusETA() {
  const url = 'http://127.0.0.1:8000/api/eta/predict-eta';
  const payload = {
    bus_id: 0,
    route_id: 0,
    latitude: 22.58656076490561,
    longitude: 88.32355563485277,
    current_speed: 38.0,
    historical_avg_speed: 40.0,
    historical_delay_minutes: 4.498095607205338,
    time_slot: 6,
    nearest_stop_index: 1,
    destination_stop_index: 2,
    distance_to_destination_km: 7.932459579115933,
    effective_speed: 39.0
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (data.success) {
      console.log(`Predicted ETA: ${data.eta_minutes.toFixed(2)} minutes`);
    }
  } catch (error) {
    console.error('ETA API Call Failed:', error);
  }
}
```

---

## 5. Prototype & Model Limitations Notice

> [!WARNING]
> **Prototype / Synthetic Target Notice:**
> The current ETA model was trained on synthetic project telemetry data (`eta_training_data.csv`) using a derived proxy ETA target calculation. As documented in [`README.md`](file:///a:/kashyap_SIH/NER_SIH/ai_backend/eta_model/README.md), reported model metrics reflect consistency against the synthetic proxy target formula and should be treated as a **prototype / demonstration endpoint** until real-world operational transit data is collected and used to retrain the model.
