from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
from src.app.schemas.analysis import ImageAnalysisResponse, BatchImageAnalysisResponse
from src.app.services.inference import InferenceEngine
from src.app.services.calibration import CalibrationService
from src.app.services.explainability import ExplainabilityEngine
from src.app.services.metadata import MetadataExtractor
from src.app.services.generator_attribution import GeneratorAttributionService

router = APIRouter()

inference_engine = InferenceEngine()
calibration_service = CalibrationService()
explainability_engine = ExplainabilityEngine()
metadata_extractor = MetadataExtractor()
generator_attribution_service = GeneratorAttributionService()

def process_single_image(image_bytes: bytes, filename: str) -> dict:
    inf_res = inference_engine.analyze_image(image_bytes, filename)
    cal_res = calibration_service.calibrate(inf_res["raw_prob_ai"])
    meta_res = metadata_extractor.inspect(image_bytes)
    exp_res = explainability_engine.generate_explanation(
        image=inf_res["image"],
        is_ai=cal_res["is_ai_generated"],
        confidence=cal_res["calibrated_confidence"],
        features_summary=inf_res["features_summary"]
    )
    attr_res = generator_attribution_service.predict_attribution(
        is_ai=cal_res["is_ai_generated"],
        raw_prob_ai=inf_res["raw_prob_ai"],
        metadata_signals=meta_res["authenticity_signals"]
    )

    return {
        "image_name": filename,
        "prediction": cal_res["verdict"],
        "is_ai_generated": cal_res["is_ai_generated"],
        "raw_probability_ai": inf_res["raw_prob_ai"],
        "calibrated_confidence": cal_res["calibrated_confidence"],
        "confidence_percentage": cal_res["confidence_percentage"],
        "convnext_features_summary": inf_res["features_summary"],
        "explanation": exp_res["explanation"],
        "gradcam_heatmap": exp_res["gradcam"],
        "generator_attribution": attr_res,
        "metadata_provenance": meta_res
    }

@router.post("/analyze", response_model=ImageAnalysisResponse, summary="Analyze Single Image Authenticity")
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image format (JPEG, PNG, WebP).")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    res = process_single_image(contents, file.filename or "uploaded_image.png")
    return res

@router.post("/analyze-batch", response_model=BatchImageAnalysisResponse, summary="Batch Image Authenticity Analysis")
async def analyze_batch(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided in batch upload.")

    results = []
    for f in files:
        if f.content_type.startswith("image/"):
            contents = await f.read()
            if contents:
                res = process_single_image(contents, f.filename or "batch_image.png")
                results.append(res)

    return {
        "total_analyzed": len(results),
        "results": results
    }
