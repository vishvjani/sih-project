"""
SignalScope PyTorch Grad-CAM Explainability Module
Computes true Gradient-weighted Class Activation Mapping (Grad-CAM)
on the ConvNeXt-Tiny feature extraction backbone.
"""

import io
import base64
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F


class ConvNeXtGradCAM:
    """
    Grad-CAM implementation tailored for ConvNeXt architectures.
    Hooks into the final convolutional stage to extract visual attribution maps.
    """
    def __init__(self, model, target_layer=None):
        self.model = model
        self.model.eval()

        # Target layer defaults to the final stage of ConvNeXt features
        if target_layer is None:
            if hasattr(model, "features") and len(model.features) > 7:
                self.target_layer = model.features[7]
            else:
                self.target_layer = list(model.features.children())[-1]
        else:
            self.target_layer = target_layer

        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(self, input_tensor: torch.Tensor, class_idx: int = 0) -> np.ndarray:
        """
        Generate raw normalized Grad-CAM heatmap [0, 1] for input tensor [1, 3, H, W].
        """
        self.model.zero_grad()
        binary_logits, _ = self.model(input_tensor)

        # Target AI class logit
        target_score = binary_logits[0, class_idx] if binary_logits.shape[-1] > 1 else binary_logits[0, 0]
        target_score.backward(retain_graph=True)

        gradients = self.gradients  # [1, C, H, W]
        activations = self.activations  # [1, C, H, W]

        if gradients is None or activations is None:
            # Fallback uniform heatmap
            return np.zeros((input_tensor.shape[2], input_tensor.shape[3]), dtype=np.float32)

        # Global average pooling on gradients across spatial dimensions
        weights = torch.mean(gradients, dim=(2, 3), keepdim=True)  # [1, C, 1, 1]
        cam = torch.sum(weights * activations, dim=1, keepdim=True)  # [1, 1, H, W]

        # Apply ReLU to retain only features with positive influence
        cam = F.relu(cam)

        # Upsample to input tensor spatial resolution
        cam = F.interpolate(cam, size=(input_tensor.shape[2], input_tensor.shape[3]), mode="bilinear", align_corners=False)
        cam = cam.squeeze().cpu().numpy()

        # Normalize between 0 and 1
        cam_min, cam_max = np.min(cam), np.max(cam)
        if cam_max - cam_min > 1e-6:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam

    def overlay_heatmap(self, original_img: Image.Image, heatmap: np.ndarray, alpha: float = 0.5, colormap: str = "jet") -> Image.Image:
        """
        Overlays normalized heatmap on the original PIL image.
        Uses procedural RGB Jet colormap to avoid heavy matplotlib dependency if needed.
        """
        orig_w, orig_h = original_img.size
        heatmap_resized = Image.fromarray((heatmap * 255).astype(np.uint8)).resize((orig_w, orig_h), Image.Resampling.BILINEAR)
        heat_np = np.array(heatmap_resized, dtype=np.float32) / 255.0

        # Simple Jet colormap computation in numpy
        r = np.clip(1.5 - np.abs(4.0 * heat_np - 3.0), 0.0, 1.0)
        g = np.clip(1.5 - np.abs(4.0 * heat_np - 2.0), 0.0, 1.0)
        b = np.clip(1.5 - np.abs(4.0 * heat_np - 1.0), 0.0, 1.0)
        color_heatmap = (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)

        color_heatmap_pil = Image.fromarray(color_heatmap).convert("RGBA")
        base_pil = original_img.convert("RGBA")

        # Blend with alpha
        blended = Image.blend(base_pil, color_heatmap_pil, alpha=alpha)
        return blended

    def to_base64(self, image: Image.Image) -> str:
        """Helper to convert PIL Image to base64 string."""
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
