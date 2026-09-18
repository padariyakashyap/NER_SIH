"""
Unified AI Backend Gateway (FastAPI)

NER-LogiAI / SIH Project

Services:
    - ETA Prediction
    - Landslide Detection
    - Route Calculation (OpenRouteService)
"""

import sys
from pathlib import Path

from fastapi import FastAPI
import uvicorn


# =====================================================
# PROJECT CONFIGURATION
# =====================================================

# Get project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ensure project root is available in Python path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =====================================================
# IMPORT ETA API
# =====================================================

try:

    from ai_backend.eta_model.predict_api import app as eta_app

except ImportError:

    from eta_model.predict_api import app as eta_app


# =====================================================
# IMPORT LANDSLIDE API
# =====================================================

try:

    from ai_backend.landslide_model.predict_api import app as landslide_app

    landslide_available = True

    landslide_status_msg = "available"

except Exception as err:

    landslide_app = None

    landslide_available = False

    landslide_status_msg = f"unavailable: {str(err)}"


# =====================================================
# IMPORT ROUTE API
# =====================================================

try:

    from ai_backend.route_api import app as route_app

    route_available = True

    route_status_msg = "available"

except Exception as err:

    route_app = None

    route_available = False

    route_status_msg = f"unavailable: {str(err)}"


# =====================================================
# IMPORT COMBINED RISK API
# =====================================================

try:

    from ai_backend.risk_model.combined_risk_api import app as combined_risk_app

    risk_available = True

    risk_status_msg = "available"

except Exception as err:

    combined_risk_app = None

    risk_available = False

    risk_status_msg = f"unavailable: {str(err)}"


from fastapi.middleware.cors import CORSMiddleware

# =====================================================
# CREATE MAIN FASTAPI APPLICATION
# =====================================================

app = FastAPI(

    title="NER-SIH Unified AI Backend API",

    description=(
        "Unified API Gateway integrating "
        "ETA prediction, landslide detection, "
        "combined risk engine, and hybrid route calculation."
    ),

    version="2.0.0"

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# MOUNT ETA API
# =====================================================

app.mount(

    "/api/eta",

    eta_app

)


# =====================================================
# MOUNT ROUTE API
# =====================================================

if route_available and route_app is not None:

    app.mount(

        "/api/routes",

        route_app

    )


# =====================================================
# MOUNT COMBINED RISK API
# =====================================================

if risk_available and combined_risk_app is not None:

    app.mount(

        "/api/risk",

        combined_risk_app

    )


# =====================================================
# MOUNT LANDSLIDE API
# =====================================================

if landslide_available and landslide_app is not None:

    app.mount(

        "/api/landslide",

        landslide_app

    )


# =====================================================
# ROOT ENDPOINT
# =====================================================

@app.get("/")
def read_root():

    return {

        "message": (
            "NER-SIH Unified AI Backend "
            "API Gateway is running"
        ),

        "services": {

            "eta": "/api/eta",

            "routes": (
                "/api/routes"
                if route_available
                else None
            ),

            "risk": (
                "/api/risk"
                if risk_available
                else None
            ),

            "landslide": (
                "/api/landslide"
                if landslide_available
                else None
            )

        },

        "docs": "/docs"

    }


# =====================================================
# HEALTH CHECK ENDPOINT
# =====================================================

@app.get("/health")
def health_check():

    return {

        "status": "ok",

        "services": {

            "eta": "available",

            "routes": route_status_msg,

            "risk": risk_status_msg,

            "landslide": landslide_status_msg

        }

    }



# =====================================================
# RUN SERVER
# =====================================================

if __name__ == "__main__":

    uvicorn.run(

        app,

        host="127.0.0.1",

        port=8000

    )