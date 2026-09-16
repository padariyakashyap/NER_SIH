from pathlib import Path
from io import BytesIO

import base64
from io import BytesIO
from PIL import Image

import torch
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from torchvision import transforms

from model import create_model


# ============================================================
# 1. APP SETUP
# ============================================================

app = FastAPI(
    title="NER-LogiAI Landslide Detection API",
    description="AI-powered landslide segmentation API",
    version="1.0.0"
)


# ============================================================
# 2. DEVICE
# ============================================================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using device:", DEVICE)


# ============================================================
# 3. MODEL PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "best_landslide_model.pth"


# ============================================================
# 4. LOAD TRAINED MODEL
# ============================================================

print("Loading trained landslide model...")

model = create_model()

checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE,
    weights_only=True
)

model.load_state_dict(checkpoint)
model.to(DEVICE)
model.eval()

print("Model loaded successfully!")


# ============================================================
# 5. IMAGE PREPROCESSING
# ============================================================

transform = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor()
])


# ============================================================
# 6. HOME ENDPOINT
# ============================================================

@app.get("/")
def home():

    return {
        "message": "NER-LogiAI Landslide Detection API is running!"
    }



def create_overlay(image, predicted_mask):
    """
    Create a red overlay showing predicted landslide areas.
    """

    image = image.copy().convert("RGBA")

    overlay = Image.new(
        "RGBA",
        image.size,
        (255, 0, 0, 0)
    )

    overlay_pixels = overlay.load()

    for y in range(image.height):
        for x in range(image.width):

            if predicted_mask[y, x] == 1:
                overlay_pixels[x, y] = (
                    255,
                    0,
                    0,
                    120
                )

    result = Image.alpha_composite(
        image,
        overlay
    )

    buffer = BytesIO()

    result.save(
        buffer,
        format="PNG"
    )

    return base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")


# ============================================================
# 7. PREDICTION ENDPOINT
# ============================================================

@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    try:

        # ----------------------------------------------------
        # Read uploaded image
        # ----------------------------------------------------

        image_bytes = await file.read()

        image = Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

        original_size = image.size

        # ----------------------------------------------------
        # Preprocess
        # ----------------------------------------------------

        input_tensor = transform(image)

        input_tensor = input_tensor.unsqueeze(0)

        input_tensor = input_tensor.to(DEVICE)

        # ----------------------------------------------------
        # Model prediction
        # ----------------------------------------------------

        with torch.no_grad():

            output = model(input_tensor)["out"]

            probabilities = torch.softmax(output, dim=1)

            prediction = torch.argmax(
                probabilities,
                dim=1
            )

        # ----------------------------------------------------
        # Extract landslide mask
        # ----------------------------------------------------

        predicted_mask = prediction[0].cpu().numpy()

        landslide_pixels = np.sum(
            predicted_mask == 1
        )

        total_pixels = predicted_mask.size

        landslide_percentage = (
            landslide_pixels / total_pixels
        ) * 100

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        landslide_probability = probabilities[
            0, 1
        ].cpu().numpy()

        predicted_confidence = (
            landslide_probability[
                predicted_mask == 1
            ].mean()
            if landslide_pixels > 0
            else 0.0
        )

        # ----------------------------------------------------
        # Detection result
        # ----------------------------------------------------

        if landslide_percentage > 1.0:

            result = "LANDSLIDE DETECTED"

        else:

            result = "NO SIGNIFICANT LANDSLIDE DETECTED"

        # ----------------------------------------------------
        # Return result
        # ----------------------------------------------------

        return {

            "filename": file.filename,

            "result": result,

            "landslide_percentage": round(
                float(landslide_percentage),
                2
            ),

            "confidence": round(
                float(predicted_confidence * 100),
                2
            ),

            "predicted_landslide_pixels": int(
                landslide_pixels
            ),

            "total_pixels": int(
                total_pixels
            ),

            "original_image_size": {
                "width": original_size[0],
                "height": original_size[1]
            },

            "overlay_image": create_overlay(
                image,
                predicted_mask
            ),
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )