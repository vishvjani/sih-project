from pydantic import BaseModel, Field
from typing import Optional, List
from src.app.schemas.analysis import ImageAnalysisResponse

class MultimodalAnalysisRequest(BaseModel):
    caption: str = Field(..., description="User provided caption or text description accompanying the image")

class MultimodalAnalysisResponse(BaseModel):
    image_analysis: ImageAnalysisResponse = Field(..., description="Standard visual authenticity detection output")
    caption: str = Field(..., description="Provided caption")
    text_image_consistency_score: float = Field(..., description="Consistency score between image content and text caption (0.0 to 1.0)")
    consistency_verdict: str = Field(..., description="Multimodal verdict (e.g. 'Consistent', 'Inconsistent / Suspicious Misalignment')")
    mismatch_reasons: List[str] = Field(default_factory=list, description="Reasons for detected inconsistency if any")
