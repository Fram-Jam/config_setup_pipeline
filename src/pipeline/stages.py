#!/usr/bin/env python3
"""
Pipeline Stages - Concrete implementations of pipeline stages.

Each stage is a self-contained unit that:
- Has clear inputs and outputs
- Can be tested in isolation
- Can be skipped or run standalone
"""

import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

from .base import PipelineStage
from ..models import (
    PipelineContext,
    UserProfile,
    AnalysisPatterns,
    ResearchResults,
    QuestionnaireAnswers,
    AnalysisResult,
    ValidationReport,
    GeneratedFile,
)

logger = logging.getLogger(__name__)
console = Console()


class SetupStage(PipelineStage):
    """First-time setup and profile loading."""
    
    name = "setup"
    description = "Setting up environment"
    
    def __init__(self, quick_mode: bool = False):
        self.quick_mode = quick_mode
    
    def run(self, context: PipelineContext) -> PipelineContext:
        from ..setup.wizard import SetupWizard
        
        wizard = SetupWizard()
        
        if self.quick_mode:
            profile = wizard.quick_setup()
        else:
            profile = wizard.ensure_setup()
        
        context.profile = UserProfile(
            name=profile.name,
            configs_path=profile.configs_path,
            discovered_configs=profile.discovered_configs,
            preferences=profile.preferences,
            api_keys_configured=profile.api_keys_configured
        )
        
        console.print(f"\n[green]Welcome, {profile.name}![/]")
        return context


class ConfigDiscoveryStage(PipelineStage):
    """Discover and analyze existing configurations."""
    
    name = "discovery"
    description = "Analyzing existing configurations"
    
    def __init__(self, configs_path: Optional[Path] = None):
        self.configs_path = configs_path
    
    def run(self, context: PipelineContext) -> PipelineContext:
        from ..analyzer.config_analyzer import ConfigAnalyzer
        
        # Determine path to analyze
        path = self.configs_path
        if not path and context.profile and context.profile.configs_path:
            path = context.profile.configs_path
        if not path:
            path = Path.home() / "claude-configs"
        
        analyzer = ConfigAnalyzer(str(path))
        patterns = analyzer.analyze()
        
        context.patterns = AnalysisPatterns(
            configs=patterns.get("configs", []),
            agents=patterns.get("agents", []),
            commands=patterns.get("commands", []),
            hooks=patterns.get("hooks", []),
            permissions=patterns.get("permissions", [])
        )
        
        if patterns.get("configs"):
            console.print(f"\n[green]Analyzed {len(patterns['configs'])} existing configs[/]")
            console.print(f"  • {len(patterns.get('agents', []))} agent patterns")
            console.print(f"  • {len(patterns.get('commands', []))} command patterns")
        else:
            console.print("\n[yellow]No existing configs found - using best practices[/]")
        
        return context


class ResearchStage(PipelineStage):
    """Research best practices from multiple sources."""
    
    name = "research"
    description = "Researching best practices"
    
    def __init__(self, deep: bool = True, skip: bool = False):
        self.deep = deep
        self._skip = skip
    
    def should_skip(self, context: PipelineContext) -> bool:
        return self._skip
    
    def run(self, context: PipelineContext) -> PipelineContext:
        from ..research.researcher import BestPracticesResearcher
        
        researcher = BestPracticesResearcher()
        results = researcher.research_all(deep=self.deep)
        
        summary = results.get("summary", {})
        context.research = ResearchResults(
            sources_analyzed=summary.get("sources_analyzed", 0),
            practices=results.get("practices", []),
            summary=summary
        )
        
        console.print(f"\n[green]Research complete![/]")
        console.print(f"  • {summary.get('sources_analyzed', 0)} sources analyzed")
        console.print(f"  • {summary.get('total_practices', 0)} best practices found")
        
        return context


class QuestionnaireStage(PipelineStage):
    """Interactive questionnaire for configuration preferences."""
    
    name = "questionnaire"
    description = "Configuration questionnaire"
    
    def __init__(self, answers_file: Optional[Path] = None):
        self.answers_file = answers_file
    
    def run(self, context: PipelineContext) -> PipelineContext:
        from ..questions.engine import QuestionEngine
        from ..models import Purpose, AutonomyLevel, SecurityLevel

        # If answers file provided, load from it (non-interactive mode)
        if self.answers_file and self.answers_file.exists():
            file_content = self.answers_file.read_text()

            # Support both JSON and YAML
            if self.answers_file.suffix in ['.yaml', '.yml']:
                try:
                    import yaml
                    answers_dict = yaml.safe_load(file_content)
                except ImportError:
                    console.print("[red]YAML support requires pyyaml: pip install pyyaml[/]")
                    raise ValueError("pyyaml not installed")
            else:
                import json
                answers_dict = json.loads(file_content)

            console.print(f"[cyan]Loaded answers from {self.answers_file}[/]")
        else:
            # Interactive mode
            patterns = context.patterns.model_dump() if context.patterns else {}
            research = context.research.model_dump() if context.research else {}

            engine = QuestionEngine(patterns, research)
            answers_dict = engine.run_questionnaire()

            if not answers_dict:
                raise ValueError("Questionnaire cancelled by user")

        # Map string values to enums with fallbacks
        def match_enum(value: str, enum_class, default):
            """Find enum by partial match or return default."""
            if not value:
                return default
            for member in enum_class:
                if value in member.value or member.value in value:
                    return member
            return default

        purpose = match_enum(
            answers_dict.get("purpose", ""),
            Purpose,
            Purpose.SOLO
        )
        autonomy = match_enum(
            answers_dict.get("autonomy_level", ""),
            AutonomyLevel,
            AutonomyLevel.SENIOR_DEV
        )
        security = match_enum(
            answers_dict.get("security_level", ""),
            SecurityLevel,
            SecurityLevel.STANDARD
        )

        context.answers = QuestionnaireAnswers(
            config_name=answers_dict.get("config_name", "new-config"),
            purpose=purpose,
            autonomy_level=autonomy,
            security_level=security,
            enable_memory=answers_dict.get("enable_memory", False),
            enable_multi_model=answers_dict.get("enable_multi_model", False),
        )

        return context
    
    def validate_input(self, context: PipelineContext) -> bool:
        # Questionnaire can run with or without prior stages
        return True


class CriticalAnalysisStage(PipelineStage):
    """Critical analysis of configuration choices."""
    
    name = "analysis"
    description = "Analyzing configuration choices"
    
    def run(self, context: PipelineContext) -> PipelineContext:
        from ..advisor.critical_advisor import CriticalAdvisor
        
        research = context.research.model_dump() if context.research else {}
        answers = context.answers.model_dump() if context.answers else {}
        
        advisor = CriticalAdvisor(research)
        analysis = advisor.analyze_choices(answers)
        
        context.analysis = AnalysisResult(
            is_valid=analysis.is_valid,
            concerns=[],  # Would need to convert Concern objects
            score=analysis.score,
            summary=analysis.summary
        )
        
        console.print(f"\n[cyan]Configuration Score: {analysis.score}/100[/]")
        console.print(f"  {analysis.summary}")
        
        # Present concerns if any
        if not advisor.present_concerns():
            raise ValueError("User declined to continue with current configuration")
        
        return context
    
    def validate_input(self, context: PipelineContext) -> bool:
        return context.answers is not None


class GenerationStage(PipelineStage):
    """Generate configuration files."""
    
    name = "generation"
    description = "Generating configuration files"
    
    def run(self, context: PipelineContext) -> PipelineContext:
        from ..generator.config_generator import ConfigGenerator
        
        patterns = context.patterns.model_dump() if context.patterns else {}
        research = context.research.model_dump() if context.research else {}
        answers = context.answers.model_dump() if context.answers else {}
        
        generator = ConfigGenerator(patterns, research)
        config = generator.generate(answers)
        
        context.generated_files = [
            GeneratedFile(
                path=f["path"],
                content=f.get("content", ""),
                description=f.get("description", "")
            )
            for f in config.get("files", [])
        ]
        
        console.print(f"\n[green]Generated {len(context.generated_files)} files[/]")
        for f in context.generated_files:
            console.print(f"  • {f.path}")
        
        return context
    
    def validate_input(self, context: PipelineContext) -> bool:
        return context.answers is not None


class ValidationStage(PipelineStage):
    """Validate generated configuration."""
    
    name = "validation"
    description = "Validating configuration"
    
    def run(self, context: PipelineContext) -> PipelineContext:
        from ..validator.config_validator import ConfigValidator
        
        validator = ConfigValidator()
        
        # Build config dict for validation
        config = {
            "answers": context.answers.model_dump() if context.answers else {},
            "files": [f.model_dump() for f in context.generated_files]
        }
        
        files_list = [
            {"path": f.path, "content": f.content}
            for f in context.generated_files
        ]
        
        report = validator.validate_generated_config(config, files_list)
        
        context.validation = ValidationReport(
            is_valid=report.is_valid,
            issues=[],  # Would convert ValidationIssue objects
            score=report.score,
            summary=report.summary,
            checks_passed=report.checks_passed,
            checks_total=report.checks_total
        )
        
        console.print(f"\n[cyan]Validation Score: {report.score}%[/]")
        console.print(f"  {report.summary}")
        
        if not report.is_valid:
            validator.print_report(report)
        
        return context
    
    def validate_input(self, context: PipelineContext) -> bool:
        return len(context.generated_files) > 0


class ReviewStage(PipelineStage):
    """Multi-model review of configuration."""
    
    name = "review"
    description = "Multi-model review"
    
    def __init__(self, skip: bool = False):
        self._skip = skip
    
    def should_skip(self, context: PipelineContext) -> bool:
        if self._skip:
            return True
        # Skip if no API keys configured
        if context.profile and not context.profile.api_keys_configured:
            console.print("\n[yellow]Skipping review - no API keys configured[/]")
            return True
        return False
    
    def run(self, context: PipelineContext) -> PipelineContext:
        from ..review.reviewer import ConfigReviewer
        
        reviewer = ConfigReviewer()
        
        config = {
            "config_name": context.answers.config_name if context.answers else "unnamed",
            "files": [f.model_dump() for f in context.generated_files],
            "answers": context.answers.model_dump() if context.answers else {}
        }
        
        results = reviewer.review(config)
        
        # Store review issues
        context.review_issues = []  # Would convert ReviewIssue objects
        
        summary = results.get("summary", {})
        console.print(f"\n[cyan]Review complete![/]")
        console.print(f"  • {summary.get('total', 0)} issues found")
        console.print(f"  • {summary.get('critical', 0)} critical")
        
        return context
    
    def validate_input(self, context: PipelineContext) -> bool:
        return len(context.generated_files) > 0


class WriteStage(PipelineStage):
    """Write configuration to disk."""
    
    name = "write"
    description = "Writing configuration files"
    
    def __init__(self, output_path: Optional[Path] = None, force: bool = False):
        self.output_path = output_path
        self.force = force
    
    def run(self, context: PipelineContext) -> PipelineContext:
        from ..generator.config_generator import ConfigGenerator
        
        # Determine output path
        path = self.output_path
        if not path and context.answers:
            path = Path.cwd() / context.answers.config_name
        if not path:
            path = Path.cwd() / "new-config"
        
        # Confirm with user unless force mode
        if not self.force:
            if not Confirm.ask(f"\nWrite configuration to [cyan]{path}[/]?", default=True):
                raise ValueError("User cancelled write operation")
        
        # Write files
        patterns = context.patterns.model_dump() if context.patterns else {}
        research = context.research.model_dump() if context.research else {}
        
        generator = ConfigGenerator(patterns, research)
        
        config = {
            "files": [f.model_dump() for f in context.generated_files],
            "answers": context.answers.model_dump() if context.answers else {}
        }
        
        generator.write_config(config, path)
        
        console.print(f"\n[green]Configuration written to: {path}[/]")
        
        return context
    
    def validate_input(self, context: PipelineContext) -> bool:
        return len(context.generated_files) > 0
