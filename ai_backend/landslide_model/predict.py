import torch
import numpy as np
import matplotlib.pyplot as plt

from PIL import Image
from pathlib import Path

from model import create_model


# ============================================================
# 1. SETTINGS
# ============================================================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

MODEL_PATH = "best_landslide_model.pth"

IMAGE_PATH = "Wenchuan/img/wenchuan002.tif"
MASK_PATH = "Wenchuan/mask/wenchuan002.TIF"


print("=" * 60)
print("LANDSLIDE PREDICTION")
print("=" * 60)

print("Using device:", DEVICE)


# ============================================================
# 2. LOAD MODEL
# ============================================================

print("\nLoading trained model...")

model = create_model()

checkpoint = torch.load(
    MODEL_PATH,
    map_location=DEVICE,
    weights_only=True
)

model.load_state_dict(checkpoint)

model.to(DEVICE)
model.eval()

print("Trained model loaded successfully!")


# ============================================================
# 3. LOAD IMAGE
# ============================================================

image_path = Path(IMAGE_PATH)
mask_path = Path(MASK_PATH)

image = Image.open(image_path).convert("RGB")
actual_mask = Image.open(mask_path)

image_array = np.array(image)
actual_mask_array = np.array(actual_mask)


print("\nImage selected:", image_path.name)
print("Mask selected:", mask_path.name)
print("Image size:", image.size)


# ============================================================
# 4. PREPARE IMAGE FOR MODEL
# ============================================================

image_tensor = torch.from_numpy(
    image_array.transpose(2, 0, 1)
).float() / 255.0

image_tensor = image_tensor.unsqueeze(0)

image_tensor = image_tensor.to(DEVICE)


# ============================================================
# 5. MODEL PREDICTION
# ============================================================

print("\nRunning model prediction...")

with torch.no_grad():

    output = model(image_tensor)["out"]

    probabilities = torch.softmax(output, dim=1)

    prediction = torch.argmax(
        probabilities,
        dim=1
    )

    # Probability of landslide class
    landslide_probability = probabilities[:, 1, :, :]

    predicted_mask = prediction.squeeze().cpu().numpy()

    confidence_map = landslide_probability.squeeze().cpu().numpy()


# ============================================================
# 6. CALCULATE RESULTS
# ============================================================

total_pixels = predicted_mask.size

predicted_landslide_pixels = np.sum(
    predicted_mask == 1
)

actual_landslide_pixels = np.sum(
    actual_mask_array == 1
)

predicted_percentage = (
    predicted_landslide_pixels / total_pixels
) * 100

actual_percentage = (
    actual_landslide_pixels / actual_mask_array.size
) * 100

# Average confidence of predicted landslide pixels
if predicted_landslide_pixels > 0:

    average_confidence = confidence_map[
        predicted_mask == 1
    ].mean() * 100

else:

    average_confidence = 0


# ============================================================
# 7. TERMINAL RESULTS
# ============================================================

print("\n" + "=" * 60)
print("LANDSLIDE PREDICTION RESULTS")
print("=" * 60)

print("Image:", image_path.name)

print(
    f"Actual landslide percentage   : {actual_percentage:.2f}%"
)

print(
    f"Predicted landslide percentage: {predicted_percentage:.2f}%"
)

print(
    f"Predicted landslide pixels    : {predicted_landslide_pixels}"
)

print(
    f"Total pixels                  : {total_pixels}"
)

print(
    f"Average prediction confidence : {average_confidence:.2f}%"
)

print("=" * 60)


# ============================================================
# 8. CREATE LANDSLIDE OVERLAY
# ============================================================

overlay = image_array.copy()

# Create a red highlight for predicted landslide areas

landslide_area = predicted_mask == 1

overlay[landslide_area] = [
    255,
    0,
    0
]


# Blend original image and prediction

blended = (
    image_array.astype(float) * 0.55
    +
    overlay.astype(float) * 0.45
)

blended = np.clip(
    blended,
    0,
    255
).astype(np.uint8)


# ============================================================
# 9. DISPLAY RESULTS
# ============================================================

plt.figure(figsize=(18, 5))


# Original image
plt.subplot(1, 4, 1)

plt.imshow(image_array)

plt.title("Original Image")

plt.axis("off")


# Actual mask
plt.subplot(1, 4, 2)

plt.imshow(
    actual_mask_array,
    cmap="gray"
)

plt.title(
    f"Actual Mask\n{actual_percentage:.2f}% landslide"
)

plt.axis("off")


# Predicted mask
plt.subplot(1, 4, 3)

plt.imshow(
    predicted_mask,
    cmap="gray"
)

plt.title(
    f"Predicted Mask\n{predicted_percentage:.2f}% landslide"
)

plt.axis("off")


# Overlay
plt.subplot(1, 4, 4)

plt.imshow(blended)

plt.title(
    f"Landslide Highlight\nConfidence: {average_confidence:.2f}%"
)

plt.axis("off")


plt.tight_layout()

plt.show()