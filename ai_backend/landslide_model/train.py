import time

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from dataset import LandslideDataset
from model import create_model


# --------------------------------------------------
# 1. Device
# --------------------------------------------------

device = torch.device("cpu")

print("=" * 60)
print("LANDSLIDE SEGMENTATION TRAINING")
print("=" * 60)
print("Using device:", device)


# --------------------------------------------------
# 2. Datasets
# --------------------------------------------------

train_dataset = LandslideDataset(
    image_dir="data/train/images",
    mask_dir="data/train/masks"
)

val_dataset = LandslideDataset(
    image_dir="data/val/images",
    mask_dir="data/val/masks"
)


# --------------------------------------------------
# 3. DataLoaders
# --------------------------------------------------

train_loader = DataLoader(
    train_dataset,
    batch_size=2,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_dataset,
    batch_size=2,
    shuffle=False,
    num_workers=0
)

print("Training batches:", len(train_loader))
print("Validation batches:", len(val_loader))


# --------------------------------------------------
# 4. Model
# --------------------------------------------------

model = create_model().to(device)


# --------------------------------------------------
# 5. Weighted loss
# --------------------------------------------------

class_weights = torch.tensor(
    [0.52549553, 10.66453974],
    dtype=torch.float32
).to(device)

criterion = torch.nn.CrossEntropyLoss(
    weight=class_weights
)


# --------------------------------------------------
# 6. Optimizer
# --------------------------------------------------

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.0001
)


# --------------------------------------------------
# 7. Metrics
# --------------------------------------------------

def calculate_metrics(predictions, masks):

    predictions = torch.argmax(predictions, dim=1)

    predictions = predictions == 1
    masks = masks == 1

    intersection = (predictions & masks).sum().item()

    prediction_pixels = predictions.sum().item()
    mask_pixels = masks.sum().item()

    union = prediction_pixels + mask_pixels - intersection

    dice = (2 * intersection) / (
        prediction_pixels + mask_pixels + 1e-8
    )

    iou = intersection / (union + 1e-8)

    return dice, iou


# --------------------------------------------------
# 8. Training settings
# --------------------------------------------------

num_epochs = 10

best_dice = 0.0

training_start = time.time()


print("\n")
print("=" * 60)
print("STARTING TRAINING")
print("=" * 60)
print("Total epochs:", num_epochs)
print()


# --------------------------------------------------
# 9. Training loop
# --------------------------------------------------

for epoch in range(num_epochs):

    epoch_start = time.time()

    model.train()

    running_train_loss = 0.0


    print(f"\n{'=' * 60}")
    print(f"EPOCH {epoch + 1}/{num_epochs}")
    print(f"{'=' * 60}")


    # ==============================================
    # TRAINING
    # ==============================================

    progress_bar = tqdm(
        train_loader,
        total=len(train_loader),
        desc=f"Training Epoch {epoch + 1}",
        unit="batch"
    )


    for batch_index, (images, masks) in enumerate(progress_bar):

        images = images.to(device)
        masks = masks.squeeze(1).long().to(device)


        # Clear gradients
        optimizer.zero_grad()


        # Forward pass
        outputs = model(images)["out"]


        # Calculate loss
        loss = criterion(outputs, masks)


        # Backpropagation
        loss.backward()


        # Update model
        optimizer.step()


        running_train_loss += loss.item()


        average_loss = (
            running_train_loss / (batch_index + 1)
        )


        # Update live progress bar
        progress_bar.set_postfix(
            batch_loss=f"{loss.item():.4f}",
            avg_loss=f"{average_loss:.4f}"
        )


    average_train_loss = (
        running_train_loss / len(train_loader)
    )


    # ==============================================
    # VALIDATION
    # ==============================================

    print("\nStarting validation...")

    model.eval()

    running_val_loss = 0.0
    total_dice = 0.0
    total_iou = 0.0


    val_progress = tqdm(
        val_loader,
        total=len(val_loader),
        desc=f"Validation Epoch {epoch + 1}",
        unit="batch"
    )


    with torch.no_grad():

        for images, masks in val_progress:

            images = images.to(device)
            masks = masks.squeeze(1).long().to(device)


            # Prediction
            outputs = model(images)["out"]


            # Validation loss
            loss = criterion(outputs, masks)

            running_val_loss += loss.item()


            # Metrics
            dice, iou = calculate_metrics(
                outputs,
                masks
            )

            total_dice += dice
            total_iou += iou


    average_val_loss = (
        running_val_loss / len(val_loader)
    )

    average_dice = (
        total_dice / len(val_loader)
    )

    average_iou = (
        total_iou / len(val_loader)
    )


    # ==============================================
    # TIME INFORMATION
    # ==============================================

    epoch_time = time.time() - epoch_start

    total_time = time.time() - training_start

    completed_epochs = epoch + 1

    average_epoch_time = total_time / completed_epochs

    remaining_epochs = num_epochs - completed_epochs

    estimated_remaining = (
        average_epoch_time * remaining_epochs
    )


    # ==============================================
    # EPOCH RESULTS
    # ==============================================

    print("\n")
    print("-" * 60)
    print(f"EPOCH {epoch + 1}/{num_epochs} RESULTS")
    print("-" * 60)

    print(
        f"Training Loss   : {average_train_loss:.4f}"
    )

    print(
        f"Validation Loss : {average_val_loss:.4f}"
    )

    print(
        f"Dice Score      : {average_dice:.4f}"
    )

    print(
        f"IoU Score       : {average_iou:.4f}"
    )

    print(
        f"Epoch Time      : {epoch_time / 60:.2f} minutes"
    )

    print(
        f"Total Time      : {total_time / 60:.2f} minutes"
    )

    print(
        f"Estimated Left  : {estimated_remaining / 60:.2f} minutes"
    )


    # ==============================================
    # SAVE BEST MODEL
    # ==============================================

    if average_dice > best_dice:

        best_dice = average_dice

        torch.save(
            model.state_dict(),
            "best_landslide_model.pth"
        )

        print(
            f"\nBEST MODEL SAVED!"
        )

        print(
            f"Best Dice: {best_dice:.4f}"
        )

    else:

        print(
            f"\nBest Dice remains: {best_dice:.4f}"
        )


    print("-" * 60)


# --------------------------------------------------
# 10. Finished
# --------------------------------------------------

total_training_time = time.time() - training_start

print("\n")
print("=" * 60)
print("TRAINING COMPLETED!")
print("=" * 60)

print(
    f"Total training time: "
    f"{total_training_time / 60:.2f} minutes"
)

print(
    f"Best validation Dice: {best_dice:.4f}"
)

print(
    "Saved model: best_landslide_model.pth"
)