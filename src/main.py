#!/usr/bin/env python3
"""
Config Setup Pipeline - Main Entry Point

A powerful tool for generating optimized Claude Code configurations through:
- Interactive questionnaire with critical feedback
- Deep research on best practices with LLM synthesis
- Learning from existing configurations
- Multi-model review of generated configs
- Comprehensive validation
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Local imports
from setup.wizard import SetupWizard
from setup.api_keys import APIKeyManager
from questions.engine import QuestionEngine
from research.researcher import BestPracticesResearcher, ResearchContext
from analyzer.config_analyzer import ConfigAnalyzer
from generator.config_generator import ConfigGenerator
from advisor.critical_advisor import CriticalAdvisor
from validator.config_validator import ConfigValidator
from review.reviewer import ConfigReviewer


VERSION = "0.3.0"


def print_banner():
    """Print welcome banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🚀 Claude Code Config Setup Pipeline v{version}                 ║
║                                                                  ║
║   Generate exceptional Claude Code configurations with:          ║
║   • Deep research on best practices                             ║
║   • Critical analysis of your choices                           ║
║   • Learning from existing configurations                        ║
║   • Multi-model review (GPT-5.2 + Gemini 3)                     ║
║   • Comprehensive validation                                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""".format(version=VERSION)
    print(banner)


def run_setup_keys(args: argparse.Namespace) -> None:
    """Run API key setup."""
    manager = APIKeyManager()
    manager.interactive_setup()


def run_interactive(args: argparse.Namespace) -> None:
    """Run interactive configuration setup."""
    print_banner()

    # Step 0: Ensure setup is complete
    print("🔧 Checking setup...")
    wizard = SetupWizard()
    profile = wizard.ensure_setup() if not args.quick else wizard.quick_setup()

    print(f"\n👋 Welcome back, {profile.name}!")

    # Step 1: Analyze existing configs
    print("\n" + "=" * 60)
    print("📊 Step 1: LEARNING FROM EXISTING CONFIGURATIONS")
    print("=" * 60)

    configs_path = Path(args.configs_path) if args.configs_path else None
    if not configs_path and profile.configs_path:
        configs_path = profile.configs_path

    analyzer = ConfigAnalyzer(str(configs_path) if configs_path else str(Path.home() / "claude-configs"))
    patterns = analyzer.analyze()

    if patterns.get("configs"):
        print(f"\n✓ Analyzed {len(patterns.get('configs', []))} existing configurations")
        print(f"   • {len(patterns.get('agents', []))} agent patterns extracted")
        print(f"   • {len(patterns.get('commands', []))} command patterns extracted")
        print(f"   • {len(patterns.get('hooks', []))} hook patterns extracted")
    else:
        print("\nℹ No existing configurations found to learn from")
        print("   That's okay - we'll use best practices from research!")

    # Step 2: Research best practices
    print("\n" + "=" * 60)
    print("🔍 Step 2: RESEARCHING BEST PRACTICES")
    print("=" * 60)

    if args.skip_research:
        print("\n⏭ Skipping research (--skip-research flag)")
        research_results = None
    else:
        researcher = BestPracticesResearcher()
        research_results = researcher.research_all(deep=not args.quick)

        summary = research_results.get("summary", {})
        print(f"\n✓ Research complete!")
        print(f"   • {summary.get('sources_analyzed', 0)} sources analyzed")
        print(f"   • {summary.get('total_practices', 0)} best practices identified")
        print(f"   • {summary.get('critical', 0)} critical practices")
        print(f"   • {summary.get('high', 0)} high-priority practices")

    # Step 3: Interactive questionnaire
    print("\n" + "=" * 60)
    print("❓ Step 3: CONFIGURATION QUESTIONNAIRE")
    print("=" * 60)

    engine = QuestionEngine(patterns, research_results)
    answers = engine.run_questionnaire()

    if not answers:
        print("\n❌ Setup cancelled.")
        return

    # Step 4: Critical analysis
    print("\n" + "=" * 60)
    print("🤔 Step 4: CRITICAL ANALYSIS")
    print("=" * 60)

    advisor = CriticalAdvisor(research_results)
    analysis = advisor.analyze_choices(answers)

    print(f"\n📊 Configuration Score: {analysis.score}/100")
    print(f"   {analysis.summary}")

    if not advisor.present_concerns():
        print("\n↩ Going back to questionnaire...")
        # In a real implementation, we'd loop back
        return

    # Step 5: Generate configuration
    print("\n" + "=" * 60)
    print("🔧 Step 5: GENERATING CONFIGURATION")
    print("=" * 60)

    generator = ConfigGenerator(patterns, research_results)
    config = generator.generate(answers)

    print(f"\n✓ Generated {len(config.get('files', []))} files")
    for f in config.get("files", []):
        print(f"   • {f['path']}")

    # Step 6: Validation
    print("\n" + "=" * 60)
    print("✅ Step 6: VALIDATION")
    print("=" * 60)

    validator = ConfigValidator()
    validation = validator.validate_generated_config(config, generator.files)

    print(f"\n📊 Validation Score: {validation.score}%")
    print(f"   {validation.summary}")

    if not validation.is_valid:
        print("\n⚠️ Validation errors found. Please review.")
        validator.print_report(validation)

        fix = input("\nAttempt to auto-fix? [Y/n]: ").strip().lower()
        if fix != 'n':
            # In production, would attempt fixes
            pass

    # Step 7: Multi-model review (optional)
    if not args.skip_review and profile.api_keys_configured:
        print("\n" + "=" * 60)
        print("🔬 Step 7: MULTI-MODEL REVIEW")
        print("=" * 60)

        reviewer = ConfigReviewer()
        review_results = reviewer.review(config)

        summary = review_results.get("summary", {})
        print(f"\n✓ Review complete!")
        print(f"   • {summary.get('total', 0)} issues found")
        print(f"   • {summary.get('critical', 0)} critical")
        print(f"   • {summary.get('high', 0)} high")

        if review_results.get("issues"):
            print("\nTop findings:")
            for issue in review_results["issues"][:3]:
                print(f"   [{issue['severity'].upper()}] {issue['message']}")

            apply = input("\nApply suggested improvements? [Y/n]: ").strip().lower()
            if apply != 'n':
                config = generator.apply_improvements(config, review_results)
                print("   ✓ Improvements applied")
    elif args.skip_review:
        print("\n⏭ Skipping review (--skip-review flag)")
    else:
        print("\n⏭ Skipping review (no API keys configured)")
        print("   Run: config-setup --setup-keys to enable multi-model review")

    # Step 8: Write configuration
    print("\n" + "=" * 60)
    print("💾 Step 8: WRITING CONFIGURATION")
    print("=" * 60)

    output_path = Path(args.output) if args.output else Path.cwd() / answers.get("config_name", "new-config")

    confirm = input(f"\nWrite configuration to {output_path}? [Y/n]: ").strip().lower()
    if confirm == 'n':
        alt_path = input("Enter alternative path: ").strip()
        if alt_path:
            output_path = Path(alt_path).expanduser()
        else:
            print("❌ Cancelled.")
            return

    generator.write_config(config, output_path)

    # Final summary
    print("\n" + "=" * 60)
    print("🎉 CONFIGURATION COMPLETE!")
    print("=" * 60)

    print(f"\n✓ Configuration created at: {output_path}")
    print(f"\nNext steps:")
    print(f"   1. Review the generated files:")
    print(f"      ls -la {output_path}")
    print(f"")
    print(f"   2. Copy to your project:")
    print(f"      cp -r {output_path}/.claude your-project/")
    print(f"      cp {output_path}/CLAUDE.md your-project/")
    print(f"")
    print(f"   3. Load your secrets (if using multi-model features):")
    print(f"      source {answers.get('secrets_location', '~/.secrets/load.sh')}")
    print(f"")
    print(f"   4. Start using Claude Code in your project!")

    print("\n" + "=" * 60)


def run_analyze(args: argparse.Namespace) -> None:
    """Analyze existing configurations."""
    print("📊 Analyzing configurations...\n")

    analyzer = ConfigAnalyzer(args.path or str(Path.home() / "claude-configs"))
    patterns = analyzer.analyze()

    if args.json:
        import json
        print(json.dumps(patterns, indent=2))
    else:
        analyzer.print_summary(patterns)


def run_research(args: argparse.Namespace) -> None:
    """Research Claude Code best practices."""
    print("🔍 Researching best practices...\n")

    context = ResearchContext()
    if args.stack:
        context.tech_stack = args.stack.split(",")

    researcher = BestPracticesResearcher(context)

    if args.topic:
        results = researcher.research_topic(args.topic, deep=not args.quick)
    else:
        results = researcher.research_all(deep=not args.quick)

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        researcher.print_summary(results)


def run_review(args: argparse.Namespace) -> None:
    """Review an existing configuration."""
    print("🔬 Reviewing configuration...\n")

    config_path = Path(args.config_path).expanduser()
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        sys.exit(1)

    # First validate
    validator = ConfigValidator()
    validation = validator.validate_path(config_path)
    validator.print_report(validation)

    # Then review with models if keys available
    wizard = SetupWizard()
    wizard.api_key_manager.load_env_file()

    if wizard.api_key_manager.get_key("openai") or wizard.api_key_manager.get_key("gemini"):
        print("\nRunning multi-model review...")
        reviewer = ConfigReviewer()
        results = reviewer.review_path(config_path)

        if args.json:
            import json
            print(json.dumps(results, indent=2))
        else:
            reviewer.print_results(results)
    else:
        print("\n💡 Enable multi-model review by setting up API keys:")
        print("   config-setup --setup-keys")


def run_validate(args: argparse.Namespace) -> None:
    """Validate an existing configuration."""
    print("✅ Validating configuration...\n")

    config_path = Path(args.config_path).expanduser()
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        sys.exit(1)

    validator = ConfigValidator()
    report = validator.validate_path(config_path)

    if args.json:
        import json
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


def run_status(args: argparse.Namespace) -> None:
    """Show current setup status."""
    print("📊 Configuration Setup Status\n")

    wizard = SetupWizard()

    # API Keys
    print("🔑 API Keys:")
    status = wizard.api_key_manager.get_status()
    for key_name, key_status in status.items():
        if key_status["configured"]:
            print(f"   ✓ {key_status['display_name']}: {key_status['masked_value']}")
        else:
            print(f"   ✗ {key_status['display_name']}: Not configured")
            print(f"      Get key at: {key_status['help_url']}")

    # Profile
    print("\n👤 Profile:")
    profile = wizard.load_profile()
    if profile:
        print(f"   Name: {profile.name}")
        print(f"   Discovered configs: {len(profile.discovered_configs)}")
        print(f"   Default autonomy: {profile.preferences.get('default_autonomy', 'not set')}")
        print(f"   Default security: {profile.preferences.get('default_security', 'not set')}")
    else:
        print("   Not configured. Run: config-setup")


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Config Setup Pipeline - Generate exceptional configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Full interactive setup
  %(prog)s --quick                  # Quick setup with sensible defaults
  %(prog)s --setup-keys             # Configure API keys only
  %(prog)s analyze ~/my-configs     # Analyze existing configs
  %(prog)s research                 # Research best practices
  %(prog)s review ./my-config       # Review and validate a config
  %(prog)s status                   # Show current setup status
        """
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    parser.add_argument(
        "--configs-path",
        help="Path to existing configs directory for learning"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory for generated config"
    )
    parser.add_argument(
        "--skip-research",
        action="store_true",
        help="Skip best practices research"
    )
    parser.add_argument(
        "--skip-review",
        action="store_true",
        help="Skip multi-model review"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick mode with sensible defaults"
    )
    parser.add_argument(
        "--setup-keys",
        action="store_true",
        help="Run API key setup"
    )

    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze existing configs")
    analyze_parser.add_argument("path", nargs="?", help="Path to analyze")
    analyze_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Research subcommand
    research_parser = subparsers.add_parser("research", help="Research best practices")
    research_parser.add_argument("--topic", help="Specific topic to research")
    research_parser.add_argument("--stack", help="Tech stack (comma-separated)")
    research_parser.add_argument("--quick", action="store_true", help="Quick research")
    research_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Review subcommand
    review_parser = subparsers.add_parser("review", help="Review a configuration")
    review_parser.add_argument("config_path", help="Path to config to review")
    review_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Validate subcommand
    validate_parser = subparsers.add_parser("validate", help="Validate a configuration")
    validate_parser.add_argument("config_path", help="Path to config to validate")
    validate_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Status subcommand
    status_parser = subparsers.add_parser("status", help="Show setup status")

    args = parser.parse_args()

    # Handle --setup-keys flag
    if args.setup_keys:
        run_setup_keys(args)
        return

    # Handle subcommands
    if args.command == "analyze":
        run_analyze(args)
    elif args.command == "research":
        run_research(args)
    elif args.command == "review":
        run_review(args)
    elif args.command == "validate":
        run_validate(args)
    elif args.command == "status":
        run_status(args)
    else:
        run_interactive(args)


if __name__ == "__main__":
    main()
