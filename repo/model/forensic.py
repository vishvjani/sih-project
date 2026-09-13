"""
SignalScope Forensic Preprocessing & Residual Stream Module
Extracts high-frequency noise residuals using Spatial Rich Model (SRM) filters
and Laplacian kernels to isolate generative artifacts and suppress semantic bias.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image


def get_srm_filters() -> torch.Tensor:
    """
    Constructs fixed Spatial Rich Model (SRM) high-pass convolution kernels.
    Kernels:
      1. 1st-order edge residual filter
      2. 2nd-order Laplacian noise filter
      3. 3x3 square spatial filter
    Filters sum to 0 to suppress low-frequency semantic information (colors, scene objects)
    and retain micro-texture/lattice noise patterns.
    """
    # Filter 1: 1st order edge filter (3x3)
    f1 = np.array([
        [ 0, -1,  0],
        [-1,  4, -1],
        [ 0, -1,  0]
    ], dtype=np.float32) / 4.0

    # Filter 2: 2nd order Laplacian (3x3)
    f2 = np.array([
        [-1,  2, -1],
        [ 2, -4,  2],
        [-1,  2, -1]
    ], dtype=np.float32) / 4.0

    # Filter 3: High-frequency square filter (3x3)
    f3 = np.array([
        [-1, -1, -1],
        [-1,  8, -1],
        [-1, -1, -1]
    ], dtype=np.float32) / 8.0

    # Shape: [3, 1, 3, 3] -> 3 output filters applied per RGB channel
    filters = np.stack([f1, f2, f3], axis=0)[:, np.newaxis, :, :]
    return torch.from_numpy(filters)


class ForensicResidualExtractor(nn.Module):
    """
    Forensic Residual Stream:
    1. Passes input image through fixed SRM high-pass filters to extract noise residuals.
    2. Uses a lightweight convolutional network to extract 256-dimensional forensic embeddings.
    """
    def __init__(self, out_features: int = 256):
        super().__init__()
        # Fixed SRM high-pass convolutional layer (3 filters per channel = 9 output channels)
        srm_weights = get_srm_filters()  # [3, 1, 3, 3]
        # Repeat across 3 RGB channels (groups=3 so each channel gets filtered independently)
        self.srm_conv = nn.Conv2d(3, 9, kernel_size=3, stride=1, padding=1, bias=False, groups=1)
        
        # Initialize SRM conv weights with fixed kernels
        kernel_9x3x3x3 = torch.zeros(9, 3, 3, 3, dtype=torch.float32)
        for i in range(3):  # 3 RGB channels
            for j in range(3):  # 3 SRM filters
                kernel_9x3x3x3[i * 3 + j, i, :, :] = srm_weights[j, 0, :, :]
        self.srm_conv.weight = nn.Parameter(kernel_9x3x3x3, requires_grad=False)

        # Forensic feature extractor network (learns noise lattice patterns)
        self.forensic_net = nn.Sequential(
            nn.Conv2d(9, 64, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, inplace=True),

            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, inplace=True),

            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, inplace=True),

            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.fc = nn.Linear(256, out_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Input: x [Batch, 3, H, W]
        Output: forensic_embeddings [Batch, out_features]
        """
        # Extract high-frequency noise residual map
        residual = self.srm_conv(x)
        # Truncate large outliers (standard steganalysis / forensic practice)
        residual = torch.clamp(residual, -3.0, 3.0)
        # Extract forensic representations
        feats = self.forensic_net(residual)
        feats = torch.flatten(feats, 1)
        out = self.fc(feats)
        return out


def extract_visual_noise_residual(image: Image.Image) -> Image.Image:
    """
    Utility function to produce a visual PIL Image of the high-frequency forensic residual.
    Useful for explainability and forensic inspection views.
    """
    img_np = np.array(image.convert("RGB"), dtype=np.float32)
    gray = np.mean(img_np, axis=2)

    # 2nd-order Laplacian high-pass filter
    kernel = np.array([
        [-1, -1, -1],
        [-1,  8, -1],
        [-1, -1, -1]
    ], dtype=np.float32)

    # Approximate convolution with border reflection
    h, w = gray.shape
    pad = np.pad(gray, 1, mode="reflect")
    residual = np.zeros_like(gray)
    for i in range(3):
        for j in range(3):
            residual += kernel[i, j] * pad[i:i+h, j:j+w]

    # Normalize to [0, 255] centered at 128
    residual_vis = np.clip((residual / 8.0) * 12.0 + 128.0, 0, 255).astype(np.uint8)
    return Image.fromarray(residual_vis, mode="L")
