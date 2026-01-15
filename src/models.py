#!/usr/bin/env python3
"""
Domain Models - Strongly-typed models for the config setup pipeline.

Uses Pydantic for validation and serialization.
"""

from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# Enums for magic strings
# =============================================================================

class Severity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    WARNING = "warning"
    SUGGESTION = "suggestion"
    INFO = "info"


class Category(str, Enum):
    """Issue/concern categories."""
    SECURITY = "security"
    BEST_PRACTICE = "best_practice"
    MISSING = "missing"
    IMPROVEMENT = "improvement"
    WORKFLOW = "workflow"
    TECH_STACK = "tech_stack"
    FEATURES = "features"
    ESSENTIALS = "essentials"


class Purpose(str, Enum):
    """Configuration purpose types."""
    SOLO = "Solo developer"
    TEAM = "Team collaboration"
    ENTERPRISE = "Enterprise/production"
    LEARNING = "Learning/experimentation"
    RESEARCH = "Research/exploration"


class AutonomyLevel(str, Enum):
    """Claude autonomy levels."""
    CO_FOUNDER = "Co-founder - High autonomy, makes decisions"
    SENIOR_DEV = "Senior dev - Suggests, waits for approval"
    ASSISTANT = "Assistant - Only does what's asked"


class SecurityLevel(str, Enum):
    """Security strictness levels."""
    RELAXED = "Relaxed - For personal projects"
    STANDARD = "Standard - Balanced safety"
    HIGH = "High - Production systems"
    MAXIMUM = "Maximum - Enterprise/regulated"


class FileDeletionPolicy(str, Enum):
    """File deletion permission policies."""
    FULL = "Yes - Can delete any file"
    LIMITED = "Limited - Only files it created"
    NONE = "No - Never delete files"


class Priority(str, Enum):
    """Best practice priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# Questionnaire Models
# =============================================================================

class TechStack(BaseModel):
    """Technology stack configuration."""
    primary_language: str = Field(description="Primary programming language")
    frameworks: list[str] = Field(default_factory=list, description="Frameworks in use")
    package_manager: str = Field(default="", description="Package manager (npm, pip, etc.)")
    database: str = Field(default="", description="Database type if any")
    test_runner: str = Field(default="", description="Test runner command")
    build_command: str = Field(default="", description="Build command")


class QuestionnaireAnswers(BaseModel):
    """Strongly-typed questionnaire answers."""
    # Basic info
    config_name: str = Field(description="Configuration name")
    identity_phrase: str = Field(default="", description="Identity confirmation phrase")
    purpose: Purpose = Field(description="Primary purpose of config")
    
    # Tech stack
    tech_stack: TechStack = Field(default_factory=TechStack)
    
    # Workflow
    autonomy_level: AutonomyLevel = Field(description="Claude's autonomy level")
    common_tasks: list[str] = Field(default_factory=list, description="Common tasks")
    
    # Security
    security_level: SecurityLevel = Field(description="Security strictness")
    allow_file_deletion: FileDeletionPolicy = Field(default=FileDeletionPolicy.LIMITED)
    
    # Features
    enable_hooks: list[str] = Field(default_factory=list, description="Enabled hooks")
    enable_agents: list[str] = Field(default_factory=list, description="Enabled agents")
    enable_commands: list[str] = Field(default_factory=list, description="Enabled commands")
    enable_memory: bool = Field(default=False, description="Enable memory system")
    enable_multi_model: bool = Field(default=False, description="Enable multi-model review")
    
    # Secrets
    has_secrets: bool = Field(default=False, description="Uses API keys/secrets")
    secrets_location: str = Field(default="~/.secrets/load.sh", description="Secrets location")


# =============================================================================
# Pipeline Context
# =============================================================================

class UserProfile(BaseModel):
    """User profile from setup wizard."""
    name: str = Field(description="User's name")
    configs_path: Optional[Path] = Field(default=None, description="Path to existing configs")
    discovered_configs: list[str] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    api_keys_configured: bool = Field(default=False)


class ResearchResults(BaseModel):
    """Results from best practices research."""
    sources_analyzed: int = Field(default=0)
    practices: list[dict] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)


class AnalysisPatterns(BaseModel):
    """Patterns extracted from existing configs."""
    configs: list[str] = Field(default_factory=list)
    agents: list[dict] = Field(default_factory=list)
    commands: list[dict] = Field(default_factory=list)
    hooks: list[dict] = Field(default_factory=list)
    permissions: list[dict] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    """A validation issue."""
    severity: Severity
    file: str
    line: Optional[int] = None
    message: str
    fix: str = ""


class ValidationReport(BaseModel):
    """Complete validation report."""
    is_valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    score: int = Field(ge=0, le=100)
    summary: str
    checks_passed: int
    checks_total: int


class Concern(BaseModel):
    """A concern from critical advisor."""
    severity: Severity
    category: Category
    message: str
    question: str
    recommendation: str
    context: str = ""


class AnalysisResult(BaseModel):
    """Result of critical analysis."""
    is_valid: bool
    concerns: list[Concern] = Field(default_factory=list)
    score: int = Field(ge=0, le=100)
    summary: str


class GeneratedFile(BaseModel):
    """A generated configuration file."""
    path: str
    content: str
    description: str = ""


class ReviewIssue(BaseModel):
    """An issue from multi-model review."""
    severity: Severity
    category: Category
    message: str
    suggestion: str
    source: str  # which model found it
    file: str = ""
    confidence: int = Field(default=80, ge=0, le=100)


class PipelineContext(BaseModel):
    """Complete context passed through the pipeline."""
    # User info
    profile: Optional[UserProfile] = None
    
    # Inputs
    answers: Optional[QuestionnaireAnswers] = None
    
    # Research & analysis
    patterns: Optional[AnalysisPatterns] = None
    research: Optional[ResearchResults] = None
    analysis: Optional[AnalysisResult] = None
    
    # Outputs
    generated_files: list[GeneratedFile] = Field(default_factory=list)
    validation: Optional[ValidationReport] = None
    review_issues: list[ReviewIssue] = Field(default_factory=list)
    
    # State
    current_stage: str = ""
    completed_stages: list[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True
