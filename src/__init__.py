"""
Config Setup Pipeline - Automated Claude Code configuration generator.

This package provides tools for:
- Interactive configuration questionnaires
- Research on Claude Code best practices
- Analysis of existing configurations
- Automated config generation with multi-model review
- Pipeline abstraction for testable, resumable execution
"""

__version__ = "0.3.0"

from .models import (
    # Enums
    Severity,
    Category,
    Purpose,
    AutonomyLevel,
    SecurityLevel,
    FileDeletionPolicy,
    Priority,
    # Models
    PipelineContext,
    QuestionnaireAnswers,
    UserProfile,
    ValidationReport,
    AnalysisResult,
)

__all__ = [
    # Enums
    "Severity",
    "Category",
    "Purpose",
    "AutonomyLevel",
    "SecurityLevel",
    "FileDeletionPolicy",
    "Priority",
    # Models
    "PipelineContext",
    "QuestionnaireAnswers",
    "UserProfile",
    "ValidationReport",
    "AnalysisResult",
]
