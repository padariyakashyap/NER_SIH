from pathlib import Path
from PIL import Image
import numpy as np
import torch
from torch.utils.data import Dataset


class LandslideDataset(Dataset):
    def __init__(self, image_dir, mask_dir):
        self.image_dir = Path(image_dir)
        self.mask_dir = Path(mask_dir)

        self.images = sorted(self.image_dir.glob("*.tif"))

        print(f"Found {len(self.images)} images")

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):
        image_path = self.images[index]

        # Find corresponding mask
        mask_path = self.mask_dir / (image_path.stem + ".TIF")

        # Load image and mask
        image = Image.open(image_path).convert("RGB")
        mask = Image.open(mask_path)

        # Convert to NumPy arrays
        image = np.array(image, dtype=np.float32) / 255.0
        mask = np.array(mask, dtype=np.float32)

        # Convert to PyTorch tensors
        image = torch.from_numpy(image).permute(2, 0, 1)
        mask = torch.from_numpy(mask).unsqueeze(0)

        return image, mask


if __name__ == "__main__":
    dataset = LandslideDataset(
        image_dir="Wenchuan/img",
        mask_dir="Wenchuan/mask"
    )

    image, mask = dataset[0]

    print("Image tensor shape:", image.shape)
    print("Mask tensor shape:", mask.shape)
    print("Image minimum:", image.min().item())
    print("Image maximum:", image.max().item())
    print("Mask unique values:", torch.unique(mask))