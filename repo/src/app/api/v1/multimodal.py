from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from src.app.schemas.multimodal import MultimodalAnalysisResponse
from src.app.api.v1.analyze import process_single_image
from src.app.services.multimodal import MultimodalChecker

router = APIRouter()
multimodal_checker = MultimodalChecker()

@router.post("/analyze-multimodal", response_model=MultimodalAnalysisResponse, summary="Multimodal Image + Caption Verification")
async def analyze_multimodal(
    caption: str = Form(..., description="Caption accompanying the image"),
    file: UploadFile = File(...)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    image_analysis = process_single_image(contents, file.filename or "image.png")
    res = multimodal_checker.check_consistency(image_analysis, caption)
    return res
