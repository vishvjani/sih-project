"""
SignalScope Dual-Stream Deep Learning Model Architecture
Combines:
  1. Semantic Stream: ConvNeXt-Tiny (Pretrained on ImageNet) - 768 features
  2. Forensic Stream: Spatial Rich Model (SRM) Noise Residual Extractor - 256 features
Fused into a unified 1024-d representation to achieve robust generalization on unseen generators
and prevent memorizing superficial generator styles.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from .forensic import ForensicResidualExtractor

try:
    import torchvision.models as models
    from torchvision.models import ConvNeXt_Tiny_Weights
    HAS_TORCHVISION = True
except ImportError:
    HAS_TORCHVISION = False


class SignalScopeModel(nn.Module):
    """
    SignalScope Dual-Stream Authenticity Detector.
    Integrates deep semantic representations from ConvNeXt-Tiny with
    high-frequency noise residual patterns from SRM filters.
    """
    def __init__(
        self,
        pretrained: bool = True,
        num_attribution_classes: int = 6,
        temperature: float = 1.15,
        dropout_rate: float = 0.3
    ):
        super().__init__()
        self.backbone_name = "ConvNeXt-Tiny + Forensic-SRM"
        self.num_attribution_classes = num_attribution_classes

        # Temperature parameter for Platt / Temperature Scaling calibration
        self.temperature = nn.Parameter(torch.tensor([temperature], dtype=torch.float32), requires_grad=False)

        # 1. Semantic Stream (ConvNeXt-Tiny)
        if HAS_TORCHVISION:
            weights = ConvNeXt_Tiny_Weights.DEFAULT if pretrained else None
            base_model = models.convnext_tiny(weights=weights)
            self.features = base_model.features
            self.avgpool = base_model.avgpool
            semantic_dim = base_model.classifier[2].in_features  # 768 for convnext_tiny
        else:
            # Fallback simple convolutional backbone if torchvision is missing
            self.features = nn.Sequential(
                nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.AdaptiveAvgPool2d((1, 1))
            )
            self.avgpool = nn.Identity()
            semantic_dim = 64

        # 2. Forensic Stream (SRM Residuals)
        forensic_dim = 256
        self.forensic_stream = ForensicResidualExtractor(out_features=forensic_dim)

        # 3. Fusion Layer
        fusion_in_dim = semantic_dim + forensic_dim  # 768 + 256 = 1024
        self.fusion = nn.Sequential(
            nn.Linear(fusion_in_dim, 512),
            nn.BatchNorm1d(512),
            nn.GELU(),
            nn.Dropout(p=dropout_rate)
        )

        # 4. Binary Authenticity Head (Logit: Real [0] vs AI [1])
        self.classifier = nn.Sequential(
            nn.Linear(512, 128),
            nn.GELU(),
            nn.Dropout(p=dropout_rate / 2),
            nn.Linear(128, 1)
        )

        # 5. Generator Attribution Head (6 Families: Real, Latent Diffusion, Flow Matching/DiT, Frontier, GAN, Novel)
        self.attribution_head = nn.Sequential(
            nn.Linear(512, 128),
            nn.GELU(),
            nn.Linear(128, num_attribution_classes)
        )

    def extract_semantic_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extracts pooled 768-d semantic representations from ConvNeXt."""
        feat_map = self.features(x)
        pooled = self.avgpool(feat_map)
        return torch.flatten(pooled, 1)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extracts and fuses both semantic and forensic features (512-d)."""
        semantic_feats = self.extract_semantic_features(x)
        forensic_feats = self.forensic_stream(x)
        combined = torch.cat([semantic_feats, forensic_feats], dim=1)
        fused = self.fusion(combined)
        return fused

    def forward(self, x: torch.Tensor):
        """
        Forward pass.
        Returns:
            binary_logits: [Batch, 1] - Raw logit for binary classification
            attribution_logits: [Batch, num_attribution_classes] - Generator attribution logits
        """
        fused = self.extract_features(x)
        binary_logits = self.classifier(fused)
        attribution_logits = self.attribution_head(fused)
        return binary_logits, attribution_logits

    def freeze_backbone(self):
        """Phase 1: Freeze ConvNeXt backbone completely. Train only forensic stream and heads."""
        for param in self.features.parameters():
            param.requires_grad = False
        for param in self.forensic_stream.parameters():
            param.requires_grad = True
        for param in self.fusion.parameters():
            param.requires_grad = True
        for param in self.classifier.parameters():
            param.requires_grad = True
        for param in self.attribution_head.parameters():
            param.requires_grad = True

    def unfreeze_later_stages(self):
        """
        Phase 2: Unfreeze Stage 3 & Stage 4 of ConvNeXt-Tiny for fine-tuning.
        Stem (index 0) and Stages 1-2 (indices 1-4) remain FROZEN to preserve
        fundamental edge/texture primitives and prevent overfitting.
        """
        if hasattr(self, "features") and len(self.features) >= 8:
            # ConvNeXt-Tiny features has 8 sequential children:
            # 0: stem, 1: stage 0, 2: downsample, 3: stage 1, 4: downsample, 5: stage 2, 6: downsample, 7: stage 3
            # Unfreeze later stages (indices 5, 6, 7)
            for idx, child in enumerate(self.features):
                requires_grad = (idx >= 5)
                for param in child.parameters():
                    param.requires_grad = requires_grad
        else:
            for param in self.features.parameters():
                param.requires_grad = True

    def extract_embeddings(self, x: torch.Tensor) -> torch.Tensor:
        """Extracts 512-d L2-normalized forensic embeddings for prototype attribution."""
        fused = self.extract_features(x)
        return F.normalize(fused, p=2, dim=1)

    def predict_calibrated(self, x: torch.Tensor):
        """
        Performs inference with Platt (Temperature Scaled) Calibration.
        Returns dictionary of numpy probability arrays and normalized embeddings.
        """
        self.eval()
        with torch.no_grad():
            fused = self.extract_features(x)
            binary_logits = self.classifier(fused)
            attribution_logits = self.attribution_head(fused)
            norm_embeddings = F.normalize(fused, p=2, dim=1)
            
            raw_prob_ai = torch.sigmoid(binary_logits)
            calibrated_logits = binary_logits / self.temperature.clamp(min=0.01)
            calibrated_prob_ai = torch.sigmoid(calibrated_logits)
            attribution_probs = F.softmax(attribution_logits, dim=-1)

            return {
                "raw_prob_ai": raw_prob_ai.cpu().numpy(),
                "calibrated_prob_ai": calibrated_prob_ai.cpu().numpy(),
                "attribution_probs": attribution_probs.cpu().numpy(),
                "embeddings": norm_embeddings.cpu().numpy()
            }

    def set_temperature(self, temp: float):
        """Update calibration temperature parameter."""
        self.temperature.data = torch.tensor([max(0.01, temp)], dtype=torch.float32, device=self.temperature.device)


def build_model(pretrained: bool = True, checkpoint_path: str = None, device: str = "cpu") -> SignalScopeModel:
    """Helper factory function to construct and load the model."""
    model = SignalScopeModel(pretrained=pretrained)
    if checkpoint_path:
        state_dict = torch.load(checkpoint_path, map_location=device)
        if "model_state_dict" in state_dict:
            model.load_state_dict(state_dict["model_state_dict"])
            if "temperature" in state_dict:
                model.set_temperature(state_dict["temperature"])
        else:
            model.load_state_dict(state_dict)
    model.to(device)
    return model
