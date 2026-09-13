from fastapi import APIRouter, File, UploadFile, HTTPException
from src.app.schemas.metadata import MetadataInspectionResponse
from src.app.services.metadata import MetadataExtractor

router = APIRouter()
metadata_extractor = MetadataExtractor()

@router.post("/inspect-metadata", response_model=MetadataInspectionResponse, summary="Inspect EXIF & Provenance Credentials")
async def inspect_metadata(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    meta = metadata_extractor.inspect(contents)

    return {
        "image_name": file.filename or "uploaded_image.png",
        "has_exif": meta["has_exif"],
        "exif_data": meta["exif_data"],
        "c2pa_detected": meta["c2pa_manifest_detected"],
        "provenance_verdict": meta["provenance_verdict"],
        "digital_signature_valid": meta["c2pa_manifest_detected"]
    }
