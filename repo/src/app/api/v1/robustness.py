from fastapi import APIRouter, File, UploadFile, HTTPException
from src.app.schemas.robustness import RobustnessTestResponse
from src.app.services.inference import InferenceEngine
from src.app.services.calibration import CalibrationService
from src.app.services.robustness import RobustnessTester

router = APIRouter()
inference_engine = InferenceEngine()
calibration_service = CalibrationService()
robustness_tester = RobustnessTester(inference_engine, calibration_service)

@router.post("/test-robustness", response_model=RobustnessTestResponse, summary="Evaluate Model Stability Under Image Degradation")
async def test_robustness(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    res = robustness_tester.test_robustness(contents, file.filename or "image.png")
    return res
