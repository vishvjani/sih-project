from fastapi import APIRouter
from src.app.services.evaluation import MetricsService
from src.app.schemas.metrics import EvaluationMetricsResponse

router = APIRouter()
metrics_service = MetricsService()

@router.get("/metrics", response_model=EvaluationMetricsResponse, summary="Get Model Evaluation Metrics (ROC-AUC & Unseen Generator Metrics)")
async def get_metrics():
    return metrics_service.get_metrics()
