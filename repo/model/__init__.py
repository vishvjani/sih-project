"""
SignalScope PyTorch Deep Learning Model Package
Designed for transfer learning, fine-tuning in Google Colab, and hybrid backend inference.
"""

from .network import SignalScopeModel
from .predict import predict_image

__all__ = ["SignalScopeModel", "predict_image"]
