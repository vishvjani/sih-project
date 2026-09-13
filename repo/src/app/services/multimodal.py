class MultimodalChecker:
    """
    Evaluates cross-modal consistency between image visual features and text caption.
    """
    def check_consistency(self, image_analysis: dict, caption: str):
        is_ai = image_analysis["is_ai_generated"]
        caption_lower = caption.lower()

        mismatch_reasons = []

        # Check claims of natural photo vs AI verdict
        if is_ai and any(word in caption_lower for word in ["authentic", "camera photo", "real shot", "untouched"]):
            mismatch_reasons.append("Caption claims authentic real-world photograph, but visual model detected AI synthetic generation indicators.")

        if not is_ai and any(word in caption_lower for word in ["ai art", "stable diffusion", "midjourney render", "synthetic"]):
            mismatch_reasons.append("Caption claims synthetic AI generation, but visual model classified image as authentic camera hardware capture.")

        score = 0.95 if len(mismatch_reasons) == 0 else 0.35
        verdict = "Consistent" if score > 0.7 else "Inconsistent / Suspicious Multimodal Misalignment"

        return {
            "image_analysis": image_analysis,
            "caption": caption,
            "text_image_consistency_score": score,
            "consistency_verdict": verdict,
            "mismatch_reasons": mismatch_reasons
        }
