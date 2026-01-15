#!/usr/bin/env python3
"""
Pipeline Base - Core pipeline abstraction.

Implements the Pipeline + Stage pattern for:
- Testable individual stages
- Resumable execution
- Non-interactive/CI support
- Plugin extensibility
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Callable

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..models import PipelineContext

logger = logging.getLogger(__name__)
console = Console()


class PipelineStage(ABC):
    """
    Abstract base class for pipeline stages.
    
    Each stage:
    - Receives a PipelineContext
    - Performs its operation
    - Returns the modified context
    - Can be skipped or run in isolation
    """
    
    name: str = "unnamed"
    description: str = ""
    
    @abstractmethod
    def run(self, context: PipelineContext) -> PipelineContext:
        """
        Execute this stage.
        
        Args:
            context: The current pipeline context
            
        Returns:
            Modified pipeline context
        """
        pass
    
    def should_skip(self, context: PipelineContext) -> bool:
        """Check if this stage should be skipped."""
        return False
    
    def validate_input(self, context: PipelineContext) -> bool:
        """Validate that required inputs are present."""
        return True
    
    def on_error(self, context: PipelineContext, error: Exception) -> PipelineContext:
        """Handle errors during stage execution."""
        logger.error(f"Stage {self.name} failed: {error}")
        return context


class Pipeline:
    """
    Orchestrates the execution of pipeline stages.
    
    Features:
    - Sequential stage execution
    - Progress tracking
    - Error handling and recovery
    - Resume from checkpoint
    - Dry-run mode
    """
    
    def __init__(
        self,
        stages: list[PipelineStage],
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ):
        self.stages = stages
        self.on_progress = on_progress
        self._current_stage_idx = 0
    
    def run(
        self,
        context: Optional[PipelineContext] = None,
        dry_run: bool = False,
        start_from: Optional[str] = None,
        stop_after: Optional[str] = None
    ) -> PipelineContext:
        """
        Run the complete pipeline.
        
        Args:
            context: Initial context (created if None)
            dry_run: If True, only validate without executing
            start_from: Stage name to start from (for resume)
            stop_after: Stage name to stop after
            
        Returns:
            Final pipeline context
        """
        if context is None:
            context = PipelineContext()
        
        # Find start index
        start_idx = 0
        if start_from:
            for i, stage in enumerate(self.stages):
                if stage.name == start_from:
                    start_idx = i
                    break
        
        total_stages = len(self.stages)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Running pipeline...", total=total_stages)
            
            for idx, stage in enumerate(self.stages[start_idx:], start=start_idx):
                self._current_stage_idx = idx
                context.current_stage = stage.name
                
                # Update progress
                progress.update(task, description=f"[cyan]{stage.description}[/]")
                
                if self.on_progress:
                    self.on_progress(stage.name, idx + 1, total_stages)
                
                # Skip check
                if stage.should_skip(context):
                    logger.info(f"Skipping stage: {stage.name}")
                    progress.advance(task)
                    continue
                
                # Validate inputs
                if not stage.validate_input(context):
                    logger.warning(f"Stage {stage.name} missing required inputs")
                    if not dry_run:
                        raise ValueError(f"Stage {stage.name} cannot run - missing inputs")
                    progress.advance(task)
                    continue
                
                # Dry run mode
                if dry_run:
                    logger.info(f"[DRY RUN] Would execute: {stage.name}")
                    progress.advance(task)
                    continue
                
                # Execute stage
                try:
                    context = stage.run(context)
                    context.completed_stages.append(stage.name)
                except Exception as e:
                    logger.error(f"Stage {stage.name} failed: {e}")
                    context = stage.on_error(context, e)
                    raise
                
                progress.advance(task)
                
                # Stop after check
                if stop_after and stage.name == stop_after:
                    logger.info(f"Stopping after stage: {stage.name}")
                    break
        
        return context
    
    def run_stage(self, stage_name: str, context: PipelineContext) -> PipelineContext:
        """Run a single stage by name."""
        for stage in self.stages:
            if stage.name == stage_name:
                return stage.run(context)
        raise ValueError(f"Stage not found: {stage_name}")
    
    def get_stage_names(self) -> list[str]:
        """Get list of all stage names."""
        return [stage.name for stage in self.stages]
    
    def validate_all(self, context: PipelineContext) -> dict[str, bool]:
        """Validate all stages without running them."""
        results = {}
        for stage in self.stages:
            results[stage.name] = stage.validate_input(context)
        return results
