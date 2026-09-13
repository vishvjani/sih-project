import numpy as np

class CalibrationService:
    """
    Applies Platt scaling / temperature scaling to raw model probabilities
    to provide calibrated, trustworthy confidence scores.
    """
    def calibrate(self, raw_prob_ai: float, temperature: float = 1.15):
        # Apply temperature scaling in logit space
        epsilon = 1e-7
        p_clipped = np.clip(raw_prob_ai, epsilon, 1 - epsilon)
        logit = np.log(p_clipped / (1 - p_clipped))
        scaled_logit = logit / temperature
        calibrated_prob_ai = float(1.0 / (1.0 + np.exp(-scaled_logit)))

        is_ai = calibrated_prob_ai >= 0.50

        if is_ai:
            verdict = "Likely AI-generated"
            confidence = calibrated_prob_ai
        else:
            verdict = "Likely Authentic Real"
            confidence = 1.0 - calibrated_prob_ai

        conf_percent_str = f"{int(round(confidence * 100))}%"

        return {
            "verdict": verdict,
            "is_ai_generated": is_ai,
            "calibrated_confidence": round(confidence, 4),
            "confidence_percentage": conf_percent_str,
            "calibrated_prob_ai": round(calibrated_prob_ai, 4)
        }
