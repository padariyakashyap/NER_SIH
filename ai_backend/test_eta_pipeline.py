"""
ETA API End-to-End Smoke Test Script

This script performs a lightweight smoke test against the unified AI backend gateway
(http://127.0.0.1:8000) using only the Python standard library (`urllib.request`, `json`).

Tests:
    1. GET  /api/eta/health
    2. POST /api/eta/predict-eta-raw
"""

import json
import sys
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000"


def main():
    print("ETA API SMOKE TEST")
    print("-" * 30)

    # 1. Test GET /api/eta/health
    health_url = f"{BASE_URL}/api/eta/health"
    try:
        req_health = urllib.request.Request(health_url)
        with urllib.request.urlopen(req_health, timeout=5) as resp:
            if resp.status == 200:
                health_data = json.loads(resp.read().decode("utf-8"))
                if health_data.get("status") == "ok":
                    print("Health: PASS")
                else:
                    print(f"Health: FAIL (Unexpected response: {health_data})")
                    sys.exit(1)
            else:
                print(f"Health: FAIL (HTTP Status {resp.status})")
                sys.exit(1)
    except urllib.error.URLError as e:
        print("ERROR: Connection failed.")
        print(f"Could not connect to ETA API at {BASE_URL}.")
        print("Please ensure the unified server is running with: python ai_backend/main.py")
        sys.exit(1)
    except Exception as e:
        print(f"Health: FAIL (Unexpected error: {str(e)})")
        sys.exit(1)

    # 2. Test POST /api/eta/predict-eta-raw
    raw_url = f"{BASE_URL}/api/eta/predict-eta-raw"
    sample_payload = {
        "bus_id": 0,
        "route_id": 0,
        "latitude": 22.58656076490561,
        "longitude": 88.32355563485277,
        "speed": 38,
        "timestamp": "2024-01-01T06:00:00",
    }

    try:
        data = json.dumps(sample_payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        req_raw = urllib.request.Request(raw_url, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req_raw, timeout=5) as resp:
            if resp.status != 200:
                print(f"Raw GPS endpoint: FAIL (HTTP Status {resp.status})")
                sys.exit(1)

            res = json.loads(resp.read().decode("utf-8"))

            # Validation checks
            success = res.get("success") is True
            eta_minutes = res.get("eta_minutes")
            is_valid_eta = isinstance(eta_minutes, (int, float)) and eta_minutes >= 0
            has_nearest = "nearest_stop_index" in res
            has_dest = "destination_stop_index" in res
            has_dist = "distance_to_destination_km" in res

            if success and is_valid_eta and has_nearest and has_dest and has_dist:
                print("Raw GPS endpoint: PASS")
                print(f"Bus ID: {res['bus_id']}")
                print(f"Route ID: {res['route_id']}")
                print(f"Nearest stop: {res['nearest_stop_index']}")
                print(f"Destination stop: {res['destination_stop_index']}")
                print(f"Distance: {res['distance_to_destination_km']:.2f} km")
                print(f"Predicted ETA: {eta_minutes:.2f} minutes")
                print("-" * 30)
                print("Overall: PASS")
            else:
                print(f"Raw GPS endpoint: FAIL (Validation check failed for response: {res})")
                sys.exit(1)

    except urllib.error.URLError as e:
        print("ERROR: Connection failed during raw prediction request.")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Raw GPS endpoint: FAIL (Unexpected error: {str(e)})")
        sys.exit(1)


if __name__ == "__main__":
    main()
