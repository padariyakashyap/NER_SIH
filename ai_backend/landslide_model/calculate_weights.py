from pathlib import Path
from PIL import Image
import numpy as np


MASK_DIR = Path("data/train/masks")

background_pixels = 0
landslide_pixels = 0

for mask_path in MASK_DIR.glob("*.TIF"):
    mask = np.array(Image.open(mask_path))

    background_pixels += np.sum(mask == 0)
    landslide_pixels += np.sum(mask == 1)

print("Background pixels:", background_pixels)
print("Landslide pixels:", landslide_pixels)

total = background_pixels + landslide_pixels

print("Total pixels:", total)

print(
    "Background percentage:",
    background_pixels / total * 100
)

print(
    "Landslide percentage:",
    landslide_pixels / total * 100
)

# Simple inverse-frequency class weights
weight_background = total / (2 * background_pixels)
weight_landslide = total / (2 * landslide_pixels)

print("\nCLASS WEIGHTS")
print("Background weight:", weight_background)
print("Landslide weight:", weight_landslide)