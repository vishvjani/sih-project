from fastapi import APIRouter
from src.app.api.v1.health import router as health_router
from src.app.api.v1.analyze import router as analyze_router
from src.app.api.v1.metadata import router as metadata_router
from src.app.api.v1.robustness import router as robustness_router
from src.app.api.v1.multimodal import router as multimodal_router
from src.app.api.v1.metrics import router as metrics_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(analyze_router, tags=["Authenticity Analysis"])
api_v1_router.include_router(metadata_router, tags=["Metadata & Provenance"])
api_v1_router.include_router(robustness_router, tags=["Robustness Testing"])
api_v1_router.include_router(multimodal_router, tags=["Multimodal Verification"])
api_v1_router.include_router(metrics_router, tags=["Model Metrics"])
