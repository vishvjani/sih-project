from pydantic import BaseModel, Field
from typing import List, Dict, Any

class EvaluationMetricsResponse(BaseModel):
    primary_metric_name: str = Field("ROC-AUC", description="Primary ranking metric")
    overall_roc_auc: float = Field(..., description="Overall ROC-AUC score across all benchmark datasets")
    unseen_generator_roc_auc: float = Field(..., description="ROC-AUC specifically evaluated on unseen generator test splits (Primary Evaluation Criterion)")
    macro_f1_score: float = Field(..., description="Macro-F1 score")
    accuracy: float = Field(..., description="Overall model classification accuracy")
    false_positive_rate: float = Field(..., description="False Positive Rate (Real images misclassified as AI)")
    confusion_matrix: Dict[str, Dict[str, int]] = Field(..., description="2x2 Confusion Matrix containing TN, FP, FN, TP counts")
    backbone_architecture: str = Field("ConvNeXt-Tiny + Transfer Learning", description="Neural backbone specification")
    unseen_generators_tested: List[str] = Field(..., description="Names of unseen generator families included in evaluation")
