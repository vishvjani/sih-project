import io
from PIL import Image

class MetadataExtractor:
    """
    Parses EXIF metadata and inspects for C2PA / Content Credentials provenance indicators.
    """
    def inspect(self, image_bytes: bytes):
        exif_dict = {}
        software = None
        camera_make_model = None
        c2pa_detected = False
        authenticity_signals = []

        try:
            image = Image.open(io.BytesIO(image_bytes))
            raw_exif = image._getexif() if hasattr(image, '_getexif') and callable(image._getexif) else None

            if raw_exif:
                for tag_id, val in raw_exif.items():
                    tag_name = str(tag_id)
                    exif_dict[tag_name] = str(val)[:100]
                    val_str = str(val).lower()

                    if "software" in tag_name.lower() or tag_id == 305:
                        software = str(val)
                    if "make" in tag_name.lower() or "model" in tag_name.lower() or tag_id in (271, 272):
                        camera_make_model = str(val)
                    if any(term in val_str for term in ["midjourney", "stable diffusion", "dall-e", "comfyui"]):
                        authenticity_signals.append(f"AI generator software tag found in EXIF: {val}")

        except Exception:
            pass

        # Check bytes directly for C2PA / Adobe Content Credentials manifest tags
        if b"c2pa" in image_bytes.lower() or b"contentcredentials" in image_bytes.lower() or b"jumbf" in image_bytes.lower():
            c2pa_detected = True
            authenticity_signals.append("C2PA / Content Credentials metadata manifest detected")

        has_exif = len(exif_dict) > 0 or software is not None or camera_make_model is not None

        if not has_exif and not c2pa_detected:
            authenticity_signals.append("Stripped metadata / No EXIF header found (common in web exports and generative models)")
        elif has_exif and camera_make_model:
            authenticity_signals.append(f"Physical camera hardware metadata present: {camera_make_model}")

        provenance_verdict = (
            "Provenanced via C2PA Digital Credentials" if c2pa_detected else
            ("Hardware EXIF Present" if camera_make_model else "No Provenance Signature (Metadata Stripped/Absent)")
        )

        return {
            "has_exif": has_exif,
            "software": software,
            "camera_make_model": camera_make_model,
            "c2pa_manifest_detected": c2pa_detected,
            "authenticity_signals": authenticity_signals,
            "exif_data": exif_dict,
            "provenance_verdict": provenance_verdict
        }
