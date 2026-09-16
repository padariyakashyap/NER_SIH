import time
from pathlib import Path

import torch
import numpy as np
from PIL import Image
from tqdm import tqdm

from model import create_model


# ============================================================
# 1. Device
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 70)
print("LANDSLIDE MODEL EVALUATION")
print("=" * 70)

print("Using device:", device)


# ============================================================
# 2. Load trained model
# ============================================================

print("\nLoading trained model...")

model = create_model()

checkpoint = torch.load(
    "best_landslide_model.pth",
    map_location=device
)

if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
    model.load_state_dict(checkpoint["model_state_dict"])
else:
    model.load_state_dict(checkpoint)

model = model.to(device)
model.eval()

print("Model loaded successfully!")


# ============================================================
# 3. Validation folders
# ============================================================

IMAGE_DIR = Path("data/val/images")
MASK_DIR = Path("data/val/masks")


image_files = sorted(IMAGE_DIR.glob("*.tif"))

if len(image_files) == 0:
    image_files = sorted(IMAGE_DIR.glob("*.TIF"))


print("\nValidation images found:", len(image_files))


# ============================================================
# 4. Metrics function
# ============================================================

def calculate_metrics(prediction, actual):

    prediction = prediction == 1
    actual = actual == 1

    true_positive = np.logical_and(
        prediction,
        actual
    ).sum()

    false_positive = np.logical_and(
        prediction,
        np.logical_not(actual)
    ).sum()

    false_negative = np.logical_and(
        np.logical_not(prediction),
        actual
    ).sum()

    intersection = true_positive

    union = (
        prediction.sum()
        + actual.sum()
        - intersection
    )

    dice = (
        (2 * intersection)
        /
        (prediction.sum() + actual.sum() + 1e-8)
    )

    iou = (
        intersection
        /
        (union + 1e-8)
    )

    precision = (
        true_positive
        /
        (true_positive + false_positive + 1e-8)
    )

    recall = (
        true_positive
        /
        (true_positive + false_negative + 1e-8)
    )

    return dice, iou, precision, recall


# ============================================================
# 5. Evaluation
# ============================================================

all_dice = []
all_iou = []
all_precision = []
all_recall = []

results = []

evaluation_start = time.time()


print("\n")
print("=" * 70)
print("STARTING EVALUATION")
print("=" * 70)
print()


progress_bar = tqdm(
    image_files,
    total=len(image_files),
    desc="Evaluating images",
    unit="image"
)


with torch.no_grad():

    for index, image_path in enumerate(progress_bar):

        start_time = time.time()


        # ----------------------------------------------------
        # Find corresponding mask
        # ----------------------------------------------------

        mask_path = MASK_DIR / (
            image_path.stem + ".TIF"
        )

        if not mask_path.exists():

            mask_path = MASK_DIR / (
                image_path.stem + ".tif"
            )


        # ----------------------------------------------------
        # Load image
        # ----------------------------------------------------

        image = Image.open(
            image_path
        ).convert("RGB")

        image_array = np.array(image)


        # ----------------------------------------------------
        # Convert image to tensor
        # ----------------------------------------------------

        image_tensor = (
            torch.from_numpy(
                image_array
            )
            .permute(2, 0, 1)
            .float()
            / 255.0
        )

        image_tensor = (
            image_tensor
            .unsqueeze(0)
            .to(device)
        )


        # ----------------------------------------------------
        # Load actual mask
        # ----------------------------------------------------

        actual_mask = np.array(
            Image.open(mask_path)
        )

        actual_mask = (
            actual_mask > 0
        ).astype(np.uint8)


        # ----------------------------------------------------
        # Model prediction
        # ----------------------------------------------------

        output = model(
            image_tensor
        )["out"]

        prediction = torch.argmax(
            output,
            dim=1
        )

        prediction = (
            prediction
            .squeeze(0)
            .cpu()
            .numpy()
        )


        # ----------------------------------------------------
        # Calculate metrics
        # ----------------------------------------------------

        dice, iou, precision, recall = calculate_metrics(
            prediction,
            actual_mask
        )


        # ----------------------------------------------------
        # Store results
        # ----------------------------------------------------

        all_dice.append(dice)
        all_iou.append(iou)
        all_precision.append(precision)
        all_recall.append(recall)


        results.append({
            "image": image_path.name,
            "dice": dice,
            "iou": iou,
            "precision": precision,
            "recall": recall
        })


        # ----------------------------------------------------
        # Time for this image
        # ----------------------------------------------------

        image_time = time.time() - start_time


        # ----------------------------------------------------
        # Update progress bar
        # ----------------------------------------------------

        progress_bar.set_postfix(
            dice=f"{dice:.3f}",
            iou=f"{iou:.3f}",
            time=f"{image_time:.1f}s"
        )


# ============================================================
# 6. Calculate averages
# ============================================================

total_time = time.time() - evaluation_start

average_dice = np.mean(all_dice)
average_iou = np.mean(all_iou)
average_precision = np.mean(all_precision)
average_recall = np.mean(all_recall)


# ============================================================
# 7. Find best and worst images
# ============================================================

best_index = np.argmax(all_dice)
worst_index = np.argmin(all_dice)

best_result = results[best_index]
worst_result = results[worst_index]


# ============================================================
# 8. Final results
# ============================================================

print("\n")
print("=" * 70)
print("FINAL EVALUATION RESULTS")
print("=" * 70)

print(
    f"Images evaluated : {len(image_files)}"
)

print(
    f"Average Dice     : {average_dice:.4f}"
)

print(
    f"Average IoU      : {average_iou:.4f}"
)

print(
    f"Average Precision: {average_precision:.4f}"
)

print(
    f"Average Recall   : {average_recall:.4f}"
)

print(
    f"Evaluation time  : {total_time / 60:.2f} minutes"
)


# ============================================================
# 9. Best image
# ============================================================

print("\n")
print("=" * 70)
print("BEST IMAGE")
print("=" * 70)

print(
    "Image:",
    best_result["image"]
)

print(
    "Dice:",
    f"{best_result['dice']:.4f}"
)

print(
    "IoU:",
    f"{best_result['iou']:.4f}"
)

print(
    "Precision:",
    f"{best_result['precision']:.4f}"
)

print(
    "Recall:",
    f"{best_result['recall']:.4f}"
)


# ============================================================
# 10. Worst image
# ============================================================

print("\n")
print("=" * 70)
print("WORST IMAGE")
print("=" * 70)

print(
    "Image:",
    worst_result["image"]
)

print(
    "Dice:",
    f"{worst_result['dice']:.4f}"
)

print(
    "IoU:",
    f"{worst_result['iou']:.4f}"
)

print(
    "Precision:",
    f"{worst_result['precision']:.4f}"
)

print(
    "Recall:",
    f"{worst_result['recall']:.4f}"
)


# ============================================================
# 11. Every image's result
# ============================================================

print("\n")
print("=" * 70)
print("INDIVIDUAL IMAGE RESULTS")
print("=" * 70)

for result in results:

    print(
        f"{result['image']:20s} | "
        f"Dice: {result['dice']:.4f} | "
        f"IoU: {result['iou']:.4f} | "
        f"Precision: {result['precision']:.4f} | "
        f"Recall: {result['recall']:.4f}"
    )


print("\n")
print("=" * 70)
print("EVALUATION COMPLETED!")
print("=" * 70)