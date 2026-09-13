import os

class Config:
    PROJECT_NAME: str = "SignalScope Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str = "Media Authenticity & AI Image Detection API with Unseen Generator Generalization, Calibrated Confidence & Explainable Grad-CAM Heatmaps"

    # Model defaults
    DEFAULT_BACKBONE: str = "ConvNeXt-Tiny"
    CALIBRATION_TEMPERATURE: float = 1.15

config = Config()
