from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

BASE = Path("Wenchuan")

image_path = BASE / "img" / "wenchuan001.tif"
mask_path = BASE / "mask" / "wenchuan001.TIF"

image = Image.open(image_path)
mask = Image.open(mask_path)

image_array = np.array(image)
mask_array = np.array(mask)

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.imshow(image_array)
plt.title("Original Image")
plt.axis("off")

plt.subplot(1, 2, 2)
plt.imshow(mask_array)
plt.title("Landslide Mask")
plt.axis("off")

plt.tight_layout()
plt.show()