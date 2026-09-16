"""
Unified AI Backend Gateway (FastAPI)

This module serves as the central entrypoint for the SIH AI Backend.
It mounts individual model REST applications (`eta_model`, `landslide_model`)
as sub-applications under distinct path prefixes (`/api/eta`, `/api/landslide`),
preserving all existing standalone inference logic and endpoints without modification.
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
import uvicorn

# Ensure project root is in sys.path when running script directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 1. Import ETA sub-application
try:
    from ai_backend.eta_model.predict_api import app as eta_app
except ImportError:
    from eta_model.predict_api import app as eta_app

# 2. Import Landslide sub-application (safely handling optional PyTorch/PIL dependencies)
try:
    from ai_backend.landslide_model.predict_api import app as landslide_app
    landslide_available = True
    landslide_status_msg = "available"
except Exception as err:
    landslide_app = None
    landslide_available = False
    landslide_status_msg = f"unavailable: {str(err)}"


# 3. Create Main Unified Application
app = FastAPI(
    title="NER-SIH Unified AI Backend API",
    description="Unified API Gateway integrating public transit ETA prediction and Landslide detection models.",
    version="1.0.0"
)


# 4. Mount sub-applications
# ETA API sub-application mounted at /api/eta
# All endpoints in eta_model/predict_api.py will be prefixed with /api/eta
app.mount("/api/eta", eta_app)

# Landslide API sub-application mounted at /api/landslide if dependencies are satisfied
if landslide_available and landslide_app is not None:
    app.mount("/api/landslide", landslide_app)


# 5. Unified Root Endpoint
@app.get("/")
def read_root():
    """Unified root endpoint identifying the combined AI Backend Gateway."""
    return {
        "message": "NER-SIH Unified AI Backend API Gateway is running",
        "services": {
            "eta": "/api/eta",
            "landslide": "/api/landslide" if landslide_available else None
        },
        "docs": "/docs"
    }


# 6. Unified Health Check Endpoint
@app.get("/health")
def health_check():
    """Unified health check status for all mounted AI services."""
    return {
        "status": "ok",
        "services": {
            "eta": "available",
            "landslide": landslide_status_msg
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
