from pydantic import BaseModel, Field
from typing import List, Dict, Any

class PerturbationResult(BaseModel):
    degradation_type: str = Field(..., description="Type of degradation applied (e.g., JPEG Compression Q=50, Resize 50%, Screenshot Crop)")
    original_prediction: str = Field(..., description="Original prediction label")
    perturbed_prediction: str = Field(..., description="Prediction label after image degradation")
    original_confidence: float = Field(..., description="Original confidence score")
    perturbed_confidence: float = Field(..., description="Confidence score after degradation")
    prediction_stable: bool = Field(..., description="Whether the prediction verdict remained stable")

class RobustnessTestResponse(BaseModel):
    image_name: str = Field(..., description="Name of the image tested")
    robustness_score: float = Field(..., description="Overall robustness score (0.0 to 1.0)")
    is_robust: bool = Field(..., description="Boolean flag indicating overall resistance to common image perturbations")
    perturbation_results: List[PerturbationResult] = Field(..., description="Breakdown of model performance across perturbations")
