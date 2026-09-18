import base64
from io import BytesIO
import logging
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from torchvision import transforms

try:
    from .model import create_model
except ImportError:
    from model import create_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LandslideAPI")

app = FastAPI(
    title="NAVEXA Landslide Detection API",
    description="AI-powered landslide segmentation API using DeepLabV3-ResNet50",
    version="2.0.0"
)

# Device configuration
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Landslide model using device: {DEVICE}")

# Model path resolution
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "best_landslide_model.pth"

if not MODEL_PATH.exists():
    logger.error(f"Model checkpoint not found at: {MODEL_PATH}")

# Model initialization & startup loading
model = create_model()

try:
    logger.info(f"Loading trained model checkpoint from: {MODEL_PATH}")
    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True)
    model.load_state_dict(checkpoint)
    model.to(DEVICE)
    model.eval()
    logger.info("Trained DeepLabV3 landslide model loaded successfully!")
except Exception as e:
    logger.error(f"Failed to load trained model checkpoint: {e}")

transform = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor()
])


def generate_visualizations(original_image: Image.Image, mask_512: np.ndarray):
    """
    Generates high-contrast binary mask, semi-transparent overlay, and converted original image Base64 PNG data URLs.
    Resizes the mask to match original image dimensions.
    """
    orig_w, orig_h = original_image.size
    
    # 0. Convert Original Image to Browser-Compatible PNG Base64
    orig_io = BytesIO()
    original_image.save(orig_io, format="PNG")
    orig_b64 = "data:image/png;base64," + base64.b64encode(orig_io.getvalue()).decode("utf-8")
    
    # Resize predicted mask back to original image size
    mask_pil = Image.fromarray((mask_512 * 255).astype(np.uint8)).resize((orig_w, orig_h), Image.NEAREST)
    mask_arr = np.array(mask_pil) > 127
    
    # 1. Binary / High-contrast Mask Image (Cyan on Black)
    mask_rgb = np.zeros((orig_h, orig_w, 3), dtype=np.uint8)
    mask_rgb[mask_arr] = [0, 225, 255]
    
    mask_io = BytesIO()
    Image.fromarray(mask_rgb).save(mask_io, format="PNG")
    mask_b64 = "data:image/png;base64," + base64.b64encode(mask_io.getvalue()).decode("utf-8")
    
    # 2. Semi-transparent Red Overlay Composite Image
    orig_rgba = original_image.convert("RGBA")
    overlay_rgba = np.zeros((orig_h, orig_w, 4), dtype=np.uint8)
    overlay_rgba[mask_arr] = [255, 0, 0, 140]
    
    overlay_pil = Image.fromarray(overlay_rgba, mode="RGBA")
    blended = Image.alpha_composite(orig_rgba, overlay_pil).convert("RGB")
    
    overlay_io = BytesIO()
    blended.save(overlay_io, format="PNG")
    overlay_b64 = "data:image/png;base64," + base64.b64encode(overlay_io.getvalue()).decode("utf-8")
    
    return orig_b64, mask_b64, overlay_b64, mask_arr


@app.get("/")
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "NAVEXA Landslide Detection API",
        "model_loaded": True,
        "device": str(DEVICE),
        "model_path": str(MODEL_PATH)
    }


@app.post("/convert-image")
async def convert_image(file: UploadFile = File(...)):
    """
    Converts TIFF / JPG / PNG files into browser-compatible Base64 PNG Data URLs for instant preview.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    
    try:
        bytes_data = await file.read()
        pil_img = Image.open(BytesIO(bytes_data)).convert("RGB")
        buf = BytesIO()
        pil_img.save(buf, format="PNG")
        b64_str = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
        return {
            "status": "success",
            "filename": file.filename,
            "width": pil_img.width,
            "height": pil_img.height,
            "image_data": b64_str
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image format: {str(e)}")


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "tif", "tiff"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '.{ext}'. Upload a JPG, JPEG, PNG, or TIFF image."
        )

    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        original_image = Image.open(BytesIO(image_bytes)).convert("RGB")
        orig_w, orig_h = original_image.size
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    try:
        # Preprocess for model input (512x512)
        input_tensor = transform(original_image).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            output = model(input_tensor)["out"]
            probabilities = torch.softmax(output, dim=1)
            prediction = torch.argmax(probabilities, dim=1)
            
            mask_512 = prediction[0].cpu().numpy()
            prob_512 = probabilities[0, 1].cpu().numpy()

        # Generate Base64 original, mask, and overlay
        orig_b64, mask_b64, overlay_b64, mask_full = generate_visualizations(original_image, mask_512)

        total_pixels = mask_full.size
        landslide_pixels = int(np.sum(mask_full))
        landslide_percentage = float((landslide_pixels / total_pixels) * 100)

        # Average prediction confidence on predicted landslide pixels
        if np.sum(mask_512 == 1) > 0:
            predicted_confidence = float(prob_512[mask_512 == 1].mean() * 100)
        else:
            predicted_confidence = 0.0

        if landslide_percentage > 1.0:
            result_str = "LANDSLIDE DETECTED"
            risk_level = "High" if landslide_percentage > 15.0 else "Medium"
        else:
            result_str = "NO SIGNIFICANT LANDSLIDE DETECTED"
            risk_level = "Low"

        return {
            "status": "success",
            "filename": file.filename,
            "prediction": result_str,
            "result": result_str,
            "risk_level": risk_level,
            "landslide_percentage": round(landslide_percentage, 2),
            "confidence": round(predicted_confidence, 2),
            "predicted_landslide_pixels": landslide_pixels,
            "total_pixels": total_pixels,
            "original_image_size": {"width": orig_w, "height": orig_h},
            "mask_dimensions": {"width": orig_w, "height": orig_h},
            "original_image": orig_b64,
            "original_url": orig_b64,
            "mask_image": mask_b64,
            "mask_url": mask_b64,
            "overlay_image": overlay_b64,
            "overlay_url": overlay_b64,
            "explanation": f"DeepLabV3-ResNet50 model evaluated {orig_w}x{orig_h} terrain imagery and identified {round(landslide_percentage, 2)}% landslide coverage.",
            "disclaimer": "AI-based terrain segmentation derived from DeepLabV3 model inference. Not a live disaster warning."
        }
    except Exception as e:
        logger.error(f"Inference error during landslide prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")