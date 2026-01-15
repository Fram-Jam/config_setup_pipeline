"""Pipeline Module - Formal pipeline abstraction with stages."""

from .base import PipelineStage, Pipeline
from .stages import (
    SetupStage,
    ConfigDiscoveryStage,
    ResearchStage,
    QuestionnaireStage,
    CriticalAnalysisStage,
    GenerationStage,
    ValidationStage,
    ReviewStage,
)

__all__ = [
    "PipelineStage",
    "Pipeline",
    "SetupStage",
    "ConfigDiscoveryStage",
    "ResearchStage",
    "QuestionnaireStage",
    "CriticalAnalysisStage",
    "GenerationStage",
    "ValidationStage",
    "ReviewStage",
]
