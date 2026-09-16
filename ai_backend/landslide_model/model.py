import torch
from torchvision.models.segmentation import (
    deeplabv3_resnet50,
    DeepLabV3_ResNet50_Weights
)
from torchvision.models.segmentation.deeplabv3 import DeepLabHead


def create_model():
    # Load pretrained DeepLabV3
    weights = DeepLabV3_ResNet50_Weights.DEFAULT

    model = deeplabv3_resnet50(weights=weights)

    # Change the final classifier for 2 classes:
    # 0 = background
    # 1 = landslide
    model.classifier = DeepLabHead(
        in_channels=2048,
        num_classes=2
    )

    return model


if __name__ == "__main__":
    model = create_model()

    print("Model created successfully!")
    print("Output classes:", 2)

    # Check the final classifier
    print(model.classifier)