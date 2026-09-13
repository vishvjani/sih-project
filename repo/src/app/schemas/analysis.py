from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GradCAMHeatmap(BaseModel):
    heatmap_base64: str = Field(..., description="Base64 encoded Grad-CAM visual heatmap overlay image")
    overlay_format: str = Field("png", description="Image format of the overlay")
    focus_regions: List[str] = Field(..., description="Localized visual evidence region descriptions")

class GroundedExplanation(BaseModel):
    summary: str = Field(..., description="Human-readable grounded summary of the visual evidence")
    detected_artifacts: List[str] = Field(..., description="List of specific visual artifacts detected")
    responsible_disclaimer: str = Field(..., description="Responsible AI likelihood-based disclaimer")

class GeneratorAttribution(BaseModel):
    predicted_family: str = Field(..., description="Predicted generator family (e.g., Diffusion, GAN, Pristine/Camera, Unseen Generator)")
    top_candidates: Dict[str, float] = Field(..., description="Likelihood probabilities across candidate generator architectures")
    predicted_model: Optional[str] = Field(None, description="Specific generative model name if identified")
    forensic_fingerprint: Optional[str] = Field(None, description="Characteristic forensic noise fingerprint")
    is_unseen_architecture: Optional[bool] = Field(None, description="Whether the architecture is an unseen or novel generator")
    attribution_rationale: Optional[str] = Field(None, description="Forensic rationale behind the model attribution")

class MetadataProvenance(BaseModel):
    has_exif: bool = Field(..., description="Whether valid EXIF metadata is present")
    software: Optional[str] = Field(None, description="Software metadata tag if present")
    camera_make_model: Optional[str] = Field(None, description="Camera make and model tag if present")
    c2pa_manifest_detected: bool = Field(..., description="Whether C2PA Content Credentials or digital signature is detected")
    authenticity_signals: List[str] = Field(..., description="Key metadata signals analyzed")

class ImageAnalysisResponse(BaseModel):
    image_name: str = Field(..., description="Filename or identifier of the analyzed image")
    prediction: str = Field(..., description="Calibrated verdict ('Likely AI-generated' or 'Likely Authentic Real')")
    is_ai_generated: bool = Field(..., description="Boolean binary classification flag")
    raw_probability_ai: float = Field(..., description="Raw model probability before calibration")
    calibrated_confidence: float = Field(..., description="Calibrated confidence score between 0.0 and 1.0 (expressed as percentage or fraction)")
    confidence_percentage: str = Field(..., description="Formatted confidence string (e.g., '88%')")
    convnext_features_summary: Dict[str, Any] = Field(..., description="Summary of visual representations extracted by ConvNeXt-Tiny backbone")
    explanation: GroundedExplanation = Field(..., description="Evidence-grounded human-readable explanation")
    gradcam_heatmap: GradCAMHeatmap = Field(..., description="Grad-CAM visualization overlay details")
    generator_attribution: GeneratorAttribution = Field(..., description="Generator family attribution signals")
    metadata_provenance: MetadataProvenance = Field(..., description="EXIF & C2PA metadata analysis")

class BatchImageAnalysisResponse(BaseModel):
    total_analyzed: int = Field(..., description="Total number of images processed")
    results: List[ImageAnalysisResponse] = Field(..., description="Individual analysis results")
