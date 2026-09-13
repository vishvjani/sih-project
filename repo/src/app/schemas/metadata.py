from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class MetadataInspectionResponse(BaseModel):
    image_name: str = Field(..., description="Name of the image file")
    has_exif: bool = Field(..., description="Presence of EXIF data")
    exif_data: Dict[str, Any] = Field(..., description="Extracted key-value EXIF metadata tags")
    c2pa_detected: bool = Field(..., description="C2PA / Content Credentials provenance status")
    provenance_verdict: str = Field(..., description="Provenance assessment summary")
    digital_signature_valid: Optional[bool] = Field(None, description="Digital signature status if present")
