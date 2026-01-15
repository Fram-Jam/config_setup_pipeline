#!/usr/bin/env python3
"""
Config Setup Pipeline CLI - Modern CLI with Typer.

Provides explicit subcommands:
- init: First-time setup
- generate: Generate new configuration
- analyze: Analyze existing configs
- research: Research best practices
- validate: Validate a configuration
- review: Multi-model review
- status: Show setup status
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="config-setup",
    help="Generate exceptional Claude Code configurations with AI-powered analysis.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()

VERSION = "0.3.0"


def print_banner():
    """Print welcome banner."""
    banner = f"""
[bold cyan]Claude Code Config Setup Pipeline[/] v{VERSION}

Generate exceptional configurations with:
• Deep research on best practices
• Critical analysis of your choices
• Learning from existing configurations
• Multi-model review (GPT-5.2 + Gemini 3)
• Comprehensive validation
"""
    console.print(Panel(banner, border_style="cyan"))


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """Claude Code Config Setup Pipeline - Generate exceptional configurations."""
    if version:
        console.print(f"config-setup v{VERSION}")
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        # Default to generate if no subcommand
        print_banner()
        console.print("\nRun [cyan]config-setup --help[/] to see available commands.\n")
        console.print("Quick start:")
        console.print("  [cyan]config-setup init[/]      - First-time setup")
        console.print("  [cyan]config-setup generate[/]  - Generate new config")
        console.print("  [cyan]config-setup analyze[/]   - Analyze existing configs")


@app.command()
def init():
    """
    First-time setup wizard.
    
    Configures API keys and discovers existing configurations.
    """
    from setup.wizard import SetupWizard
    
    print_banner()
    console.print("\n[bold]First-Time Setup[/]\n")
    
    wizard = SetupWizard()
    profile = wizard.run_setup()
    
    console.print(f"\n[green]Setup complete![/] Welcome, {profile.name}!")
    console.print("\nNext: Run [cyan]config-setup generate[/] to create your first config.")


@app.command()
def generate(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    quick: bool = typer.Option(False, "--quick", "-q", help="Quick mode with defaults"),
    skip_research: bool = typer.Option(False, "--skip-research", help="Skip best practices research"),
    skip_review: bool = typer.Option(False, "--skip-review", help="Skip multi-model review"),
    answers_file: Optional[Path] = typer.Option(None, "--answers", "-a", help="Load answers from YAML/JSON file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files"),
):
    """
    Generate a new Claude Code configuration.
    
    Runs the full pipeline: research → questionnaire → analysis → generation → validation → review.
    """
    from pipeline import (
        Pipeline,
        SetupStage,
        ConfigDiscoveryStage,
        ResearchStage,
        QuestionnaireStage,
        CriticalAnalysisStage,
        GenerationStage,
        ValidationStage,
        ReviewStage,
    )
    from pipeline.stages import WriteStage
    
    print_banner()
    
    # Build pipeline
    stages = [
        SetupStage(quick_mode=quick),
        ConfigDiscoveryStage(),
        ResearchStage(deep=not quick, skip=skip_research),
        QuestionnaireStage(answers_file=answers_file),
        CriticalAnalysisStage(),
        GenerationStage(),
        ValidationStage(),
        ReviewStage(skip=skip_review),
        WriteStage(output_path=output, force=dry_run),  # In dry-run, don't actually write
    ]
    
    pipeline = Pipeline(stages)
    
    try:
        if dry_run:
            console.print("\n[yellow]DRY RUN MODE - No files will be written[/]\n")
        
        context = pipeline.run(dry_run=dry_run)
        
        # Final summary
        console.print("\n" + "=" * 60)
        console.print("[bold green]CONFIGURATION COMPLETE![/]")
        console.print("=" * 60)
        
        if not dry_run and context.answers:
            output_path = output or Path.cwd() / context.answers.config_name
            console.print(f"\nConfiguration created at: [cyan]{output_path}[/]")
            console.print("\nNext steps:")
            console.print(f"  1. Review: [cyan]ls -la {output_path}[/]")
            console.print(f"  2. Copy to project: [cyan]cp -r {output_path}/.claude your-project/[/]")
            console.print(f"  3. Start using Claude Code!")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/]")
        logger.exception("Pipeline failed")
        raise typer.Exit(1)


@app.command()
def analyze(
    path: Optional[Path] = typer.Argument(None, help="Path to analyze"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Analyze existing Claude Code configurations.
    
    Discovers patterns, agents, commands, and hooks from existing configs.
    """
    import json
    from analyzer.config_analyzer import ConfigAnalyzer
    
    analyze_path = path or Path.home() / "claude-configs"
    
    console.print(f"\n[cyan]Analyzing configurations in:[/] {analyze_path}\n")
    
    analyzer = ConfigAnalyzer(str(analyze_path))
    patterns = analyzer.analyze()
    
    if json_output:
        print(json.dumps(patterns, indent=2))
    else:
        analyzer.print_summary(patterns)


@app.command()
def research(
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Specific topic to research"),
    stack: Optional[str] = typer.Option(None, "--stack", "-s", help="Tech stack (comma-separated)"),
    quick: bool = typer.Option(False, "--quick", "-q", help="Quick research mode"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Research Claude Code best practices.
    
    Searches official docs, GitHub, and community resources.
    """
    import json
    from research.researcher import BestPracticesResearcher, ResearchContext
    
    console.print("\n[cyan]Researching best practices...[/]\n")
    
    context = ResearchContext()
    if stack:
        context.tech_stack = stack.split(",")
    
    researcher = BestPracticesResearcher(context)
    
    if topic:
        results = researcher.research_topic(topic, deep=not quick)
    else:
        results = researcher.research_all(deep=not quick)
    
    if json_output:
        print(json.dumps(results, indent=2))
    else:
        researcher.print_summary(results)


@app.command()
def validate(
    config_path: Path = typer.Argument(..., help="Path to configuration"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Validate an existing configuration.
    
    Checks syntax, security patterns, and best practices compliance.
    """
    import json
    from validator.config_validator import ConfigValidator
    
    if not config_path.exists():
        console.print(f"[red]Config not found:[/] {config_path}")
        raise typer.Exit(1)
    
    console.print(f"\n[cyan]Validating:[/] {config_path}\n")
    
    validator = ConfigValidator()
    report = validator.validate_path(config_path)
    
    if json_output:
        print(json.dumps({
            "is_valid": report.is_valid,
            "score": report.score,
            "summary": report.summary,
            "issues": [
                {"severity": i.severity, "file": i.file, "message": i.message}
                for i in report.issues
            ]
        }, indent=2))
    else:
        validator.print_report(report)


@app.command()
def review(
    config_path: Path = typer.Argument(..., help="Path to configuration"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Multi-model review of a configuration.
    
    Uses GPT-5.2 and Gemini 3 to analyze for security and best practices.
    Requires API keys to be configured.
    """
    import json
    from validator.config_validator import ConfigValidator
    from review.reviewer import ConfigReviewer
    from setup.wizard import SetupWizard
    
    if not config_path.exists():
        console.print(f"[red]Config not found:[/] {config_path}")
        raise typer.Exit(1)
    
    console.print(f"\n[cyan]Reviewing:[/] {config_path}\n")
    
    # First validate
    validator = ConfigValidator()
    validation = validator.validate_path(config_path)
    validator.print_report(validation)
    
    # Check API keys
    wizard = SetupWizard()
    wizard.api_key_manager.load_env_file()
    
    if wizard.api_key_manager.get_key("openai") or wizard.api_key_manager.get_key("gemini"):
        console.print("\n[cyan]Running multi-model review...[/]")
        reviewer = ConfigReviewer()
        results = reviewer.review_path(config_path)
        
        if json_output:
            print(json.dumps(results, indent=2))
        else:
            reviewer.print_results(results)
    else:
        console.print("\n[yellow]Multi-model review requires API keys.[/]")
        console.print("Run: [cyan]config-setup init[/] to configure API keys.")


@app.command()
def status():
    """
    Show current setup status.
    
    Displays configured API keys, profile, and discovered configs.
    """
    from setup.wizard import SetupWizard
    
    console.print("\n[bold]Configuration Setup Status[/]\n")
    
    wizard = SetupWizard()
    
    # API Keys
    table = Table(title="API Keys", show_header=True)
    table.add_column("Service", style="cyan")
    table.add_column("Status")
    table.add_column("Value")
    
    key_status = wizard.api_key_manager.get_status()
    for key_name, info in key_status.items():
        status_icon = "[green]Configured[/]" if info["configured"] else "[red]Not set[/]"
        value = info.get("masked_value", "-") if info["configured"] else f"Get key at: {info['help_url']}"
        table.add_row(info["display_name"], status_icon, value)
    
    console.print(table)
    
    # Profile
    profile = wizard.load_profile()
    if profile:
        console.print(f"\n[bold]Profile:[/] {profile.name}")
        console.print(f"  Discovered configs: {len(profile.discovered_configs)}")
        if profile.preferences:
            console.print(f"  Default autonomy: {profile.preferences.get('default_autonomy', 'not set')}")
            console.print(f"  Default security: {profile.preferences.get('default_security', 'not set')}")
    else:
        console.print("\n[yellow]No profile configured.[/] Run: [cyan]config-setup init[/]")


@app.command()
def upgrade(
    config_path: Path = typer.Argument(..., help="Path to existing configuration"),
    diff: bool = typer.Option(True, "--diff/--no-diff", help="Show diff before applying"),
):
    """
    Upgrade an existing configuration.
    
    Analyzes current config and suggests improvements based on latest best practices.
    """
    console.print(f"\n[cyan]Upgrade feature coming soon![/]")
    console.print(f"\nThis will:")
    console.print("  • Analyze your current config at [cyan]{config_path}[/]")
    console.print("  • Research latest best practices")
    console.print("  • Show a diff of proposed changes")
    console.print("  • Let you selectively apply improvements")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
