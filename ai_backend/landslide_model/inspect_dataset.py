from pathlib import Path
from PIL import Image
import numpy as np

BASE = Path("Wenchuan")

image_path = BASE / "img" / "wenchuan001.tif"
mask_path = BASE / "mask" / "wenchuan001.TIF"

image = Image.open(image_path)
mask = Image.open(mask_path)

image_array = np.array(image)
mask_array = np.array(mask)

print("IMAGE")
print("Size:", image.size)
print("Mode:", image.mode)
print("Shape:", image_array.shape)
print("Data type:", image_array.dtype)

print("\nMASK")
print("Size:", mask.size)
print("Mode:", mask.mode)
print("Shape:", mask_array.shape)
print("Data type:", mask_array.dtype)

print("\nMask unique values:")
print(np.unique(mask_array))

print("\nLandslide pixels:")
print(np.sum(mask_array == 1))

print("Total pixels:")
print(mask_array.size)

print("Landslide percentage:")
print((np.sum(mask_array == 1) / mask_array.size) * 100)