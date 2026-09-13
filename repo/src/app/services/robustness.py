import io
from PIL import Image
import numpy as np
from src.app.services.inference import InferenceEngine
from src.app.services.calibration import CalibrationService

class RobustnessTester:
    """
    Evaluates detector stability against image degradation techniques:
    1. Severe JPEG compression (Quality = 50)
    2. Image Resizing (Downscaling by 50%)
    3. Screenshot cropping / resampling
    """
    def __init__(self, inference_engine: InferenceEngine, calibration_service: CalibrationService):
        self.inference_engine = inference_engine
        self.calibration_service = calibration_service

    def test_robustness(self, image_bytes: bytes, filename: str = "image.png"):
        # Original analysis
        orig_inf = self.inference_engine.analyze_image(image_bytes, filename)
        orig_cal = self.calibration_service.calibrate(orig_inf["raw_prob_ai"])
        orig_pred = orig_cal["verdict"]
        orig_conf = orig_cal["calibrated_confidence"]

        orig_img = orig_inf["image"]
        results = []
        stable_count = 0

        # Test 1: Severe JPEG Compression
        jpeg_io = io.BytesIO()
        orig_img.save(jpeg_io, format="JPEG", quality=50)
        jpeg_bytes = jpeg_io.getvalue()
        jpeg_inf = self.inference_engine.analyze_image(jpeg_bytes, filename)
        jpeg_cal = self.calibration_service.calibrate(jpeg_inf["raw_prob_ai"])
        jpeg_stable = jpeg_cal["verdict"] == orig_pred
        if jpeg_stable: stable_count += 1

        results.append({
            "degradation_type": "JPEG Compression (Quality=50)",
            "original_prediction": orig_pred,
            "perturbed_prediction": jpeg_cal["verdict"],
            "original_confidence": orig_conf,
            "perturbed_confidence": jpeg_cal["calibrated_confidence"],
            "prediction_stable": jpeg_stable
        })

        # Test 2: Downscaling by 50%
        w, h = orig_img.size
        resized_img = orig_img.resize((max(1, w // 2), max(1, h // 2)), Image.Resampling.BILINEAR)
        res_io = io.BytesIO()
        resized_img.save(res_io, format="PNG")
        res_bytes = res_io.getvalue()
        res_inf = self.inference_engine.analyze_image(res_bytes, filename)
        res_cal = self.calibration_service.calibrate(res_inf["raw_prob_ai"])
        res_stable = res_cal["verdict"] == orig_pred
        if res_stable: stable_count += 1

        results.append({
            "degradation_type": "50% Downscaling Perturbation",
            "original_prediction": orig_pred,
            "perturbed_prediction": res_cal["verdict"],
            "original_confidence": orig_conf,
            "perturbed_confidence": res_cal["calibrated_confidence"],
            "prediction_stable": res_stable
        })

        # Test 3: Screenshot Resampling simulation (RGB offset + center crop)
        cw, ch = int(w * 0.9), int(h * 0.9)
        crop_img = orig_img.crop((0, 0, cw, ch))
        crop_io = io.BytesIO()
        crop_img.save(crop_io, format="JPEG", quality=80)
        crop_bytes = crop_io.getvalue()
        crop_inf = self.inference_engine.analyze_image(crop_bytes, filename)
        crop_cal = self.calibration_service.calibrate(crop_inf["raw_prob_ai"])
        crop_stable = crop_cal["verdict"] == orig_pred
        if crop_stable: stable_count += 1

        results.append({
            "degradation_type": "Screenshot & Crop Resampling",
            "original_prediction": orig_pred,
            "perturbed_prediction": crop_cal["verdict"],
            "original_confidence": orig_conf,
            "perturbed_confidence": crop_cal["calibrated_confidence"],
            "prediction_stable": crop_stable
        })

        robustness_score = round(stable_count / 3.0, 2)
        is_robust = robustness_score >= 0.66

        return {
            "image_name": filename,
            "robustness_score": robustness_score,
            "is_robust": is_robust,
            "perturbation_results": results
        }
