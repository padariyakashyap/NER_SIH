import torch

from dataset import LandslideDataset
from model import create_model


# Use CPU
device = torch.device("cpu")

# Load one sample
dataset = LandslideDataset(
    image_dir="Wenchuan/img",
    mask_dir="Wenchuan/mask"
)

image, mask = dataset[0]

# Add batch dimension
image = image.unsqueeze(0).to(device)

# Create model
model = create_model()
model = model.to(device)

# Evaluation mode
model.eval()

# Run one image through the model
with torch.no_grad():
    output = model(image)

# Get segmentation output
prediction = output["out"]

print("\nMODEL TEST")
print("Input shape:", image.shape)
print("Output shape:", prediction.shape)
print("Output minimum:", prediction.min().item())
print("Output maximum:", prediction.max().item())