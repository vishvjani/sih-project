"""
SignalScope Prediction Interface Contract (SIH 2026 Core Interface)
Complies with SIH Problem Statement Section 4.1 & Section 7.1:
Accepts an image (path, bytes, or PIL Image) and returns:
  - Binary Verdict ("Likely AI-generated" or "Likely Authentic Real")
  - Calibrated Confidence Score (%)
  - Grad-CAM Heatmap Overlay
  - Generator Family Attribution
"""

import io
import os
from pathlib import Path
from typing import Union, Dict, Any
import numpy as np
from PIL import Image
import torch

from .network import SignalScopeModel, build_model
from .gradcam import ConvNeXtGradCAM

# Global cached model instance for low-latency repeated predictions
_GLOBAL_MODEL = None
_GLOBAL_GRADCAM = None

try:
    from torchvision import transforms
    _TRANSFORM = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
except ImportError:
    def _TRANSFORM(image: Image.Image) -> torch.Tensor:
        resized = image.resize((224, 224))
        arr = np.array(resized, dtype=np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm = (arr - mean) / std
        tensor = torch.from_numpy(norm.transpose(2, 0, 1))
        return tensor

ATTRIBUTION_LABELS = {
    0: "Pristine Authentic Camera Sensor",
    1: "Latent Diffusion Architecture (SD / Midjourney / Flux)",
    2: "Generative Adversarial Network (StyleGAN / ProGAN)",
    3: "Autoregressive / Novel Synthesis Family"
}


def get_inference_model(weights_path: str = None, device: str = None) -> SignalScopeModel:
    """Returns singleton instance of model, caching on chosen device."""
    global _GLOBAL_MODEL, _GLOBAL_GRADCAM

    if _GLOBAL_MODEL is not None:
        return _GLOBAL_MODEL

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    default_weights = Path(__file__).parent / "weights" / "signalscope_convnext_tiny.pth"
    chosen_path = weights_path if (weights_path and os.path.exists(weights_path)) else (str(default_weights) if default_weights.exists() else None)

    try:
        model = build_model(pretrained=(chosen_path is None), checkpoint_path=chosen_path, device=device)
        model.eval()
        _GLOBAL_MODEL = model
        _GLOBAL_GRADCAM = ConvNeXtGradCAM(model)
    except Exception as e:
        print(f"Warning: Failed to load PyTorch ConvNeXt weights ({e}). Initializing unweighted architecture.")
        model = SignalScopeModel(pretrained=False).to(device)
        model.eval()
        _GLOBAL_MODEL = model
        _GLOBAL_GRADCAM = ConvNeXtGradCAM(model)

    return _GLOBAL_MODEL


def predict_image(
    image_input: Union[str, Path, bytes, Image.Image],
    weights_path: str = None,
    device: str = None
) -> Dict[str, Any]:
    """
    Core SIH Predict Interface.
    Accepts:
      image_input: Path to file, raw image bytes, or PIL Image.
    Returns:
      Dictionary containing verdict, calibrated confidence, Grad-CAM heatmap base64, and attribution.
    """
    # 1. Parse Image
    if isinstance(image_input, (str, Path)):
        image = Image.open(str(image_input)).convert("RGB")
    elif isinstance(image_input, bytes):
        image = Image.open(io.BytesIO(image_input)).convert("RGB")
    elif isinstance(image_input, Image.Image):
        image = image_input.convert("RGB")
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    # 2. Get Model & Preprocess
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    model = get_inference_model(weights_path=weights_path, device=device)
    tensor = _TRANSFORM(image).unsqueeze(0).to(device)

    # 3. Model Inference with Platt Calibration
    with torch.no_grad():
        bin_logits, attr_logits = model(tensor)
        raw_prob = float(torch.sigmoid(bin_logits).squeeze().cpu().item())
        calib_prob = float(torch.sigmoid(bin_logits / model.temperature.clamp(min=0.01)).squeeze().cpu().item())

        attr_probs = torch.softmax(attr_logits, dim=-1).squeeze().cpu().numpy()
        pred_attr_idx = int(attr_probs.argmax())

    is_ai = calib_prob >= 0.5
    verdict = "Likely AI-generated" if is_ai else "Likely Authentic Real"
    confidence = calib_prob if is_ai else (1.0 - calib_prob)

    # 4. Compute Real Grad-CAM Explainability
    global _GLOBAL_GRADCAM
    if _GLOBAL_GRADCAM is None:
        _GLOBAL_GRADCAM = ConvNeXtGradCAM(model)

    heatmap_arr = _GLOBAL_GRADCAM.generate_heatmap(tensor, class_idx=0)
    blended_img = _GLOBAL_GRADCAM.overlay_heatmap(image, heatmap_arr, alpha=0.45)
    heatmap_base64 = _GLOBAL_GRADCAM.to_base64(blended_img)

    attribution_name = ATTRIBUTION_LABELS.get(pred_attr_idx, "Unknown Synthetic Architecture")
    if not is_ai:
        attribution_name = ATTRIBUTION_LABELS[0]

    return {
        "verdict": verdict,
        "is_ai_generated": is_ai,
        "raw_probability_ai": round(raw_prob, 4),
        "calibrated_confidence": round(confidence, 4),
        "confidence_percentage": round(confidence * 100.0, 2),
        "generator_attribution": {
            "predicted_family": attribution_name,
            "class_probabilities": {
                ATTRIBUTION_LABELS[i]: round(float(attr_probs[i]), 4) for i in range(len(ATTRIBUTION_LABELS))
            }
        },
        "gradcam_heatmap_base64": heatmap_base64,
        "features_summary": {
            "backbone": "ConvNeXt-Tiny",
            "device": str(device),
            "input_resolution": f"{image.width}x{image.height}",
            "calibrated_temperature": round(float(model.temperature.item()), 4)
        }
    }
