from pathlib import Path
import random
import shutil

random.seed(42)

BASE = Path("Wenchuan")
IMAGE_DIR = BASE / "img"
MASK_DIR = BASE / "mask"

OUTPUT = Path("data")

train_img = OUTPUT / "train" / "images"
train_mask = OUTPUT / "train" / "masks"

val_img = OUTPUT / "val" / "images"
val_mask = OUTPUT / "val" / "masks"

for folder in [train_img, train_mask, val_img, val_mask]:
    folder.mkdir(parents=True, exist_ok=True)

images = sorted(IMAGE_DIR.glob("*.tif"))

random.shuffle(images)

split_index = int(len(images) * 0.8)

train_images = images[:split_index]
val_images = images[split_index:]

print("Total images:", len(images))
print("Training images:", len(train_images))
print("Validation images:", len(val_images))

for image_path in train_images:
    mask_path = MASK_DIR / (image_path.stem + ".TIF")

    shutil.copy2(image_path, train_img / image_path.name)
    shutil.copy2(mask_path, train_mask / mask_path.name)

for image_path in val_images:
    mask_path = MASK_DIR / (image_path.stem + ".TIF")

    shutil.copy2(image_path, val_img / image_path.name)
    shutil.copy2(mask_path, val_mask / mask_path.name)

print("\nDataset split completed!")