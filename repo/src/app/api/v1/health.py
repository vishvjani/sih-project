from fastapi import APIRouter

router = APIRouter()

@router.get("/health", summary="System Health & Capability Check")
async def health_check():
    return {
        "status": "online",
        "system": "SignalScope Media Authenticity API",
        "version": "1.0.0",
        "backbone": "ConvNeXt-Tiny + Transfer Learning",
        "capabilities": [
            "Binary Image Authenticity Classification",
            "Unseen AI Generator Generalization",
            "Platt-Calibrated Confidence Scoring",
            "Grad-CAM Heatmap Localized Visual Explanations",
            "Evidence-Grounded Human Explanations",
            "Generator Attribution Analysis",
            "EXIF & C2PA Provenance Metadata Inspection",
            "Robustness Degradation Perturbation Testing",
            "Multimodal Image-Text Consistency Verification"
        ]
    }
