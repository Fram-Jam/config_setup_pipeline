#!/usr/bin/env python3
"""
Config Setup Pipeline - Main Entry Point

Interactive CLI for generating Claude Code configurations with:
- Guided questionnaire
- Deep research on best practices
- Learning from existing configs
- Multi-model review of generated configs
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Local imports
from questions.engine import QuestionEngine
from research.researcher import BestPracticesResearcher
from analyzer.config_analyzer import ConfigAnalyzer
from generator.config_generator import ConfigGenerator
from review.reviewer import ConfigReviewer


def print_banner():
    """Print welcome banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🚀 Claude Code Config Setup Pipeline                          ║
║                                                                  ║
║   Automated configuration generation with:                      ║
║   • Interactive questionnaire                                   ║
║   • Deep research on best practices                            ║
║   • Learning from your existing configs                        ║
║   • Multi-model review (GPT-5.2 + Gemini 3)                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def run_interactive(args: argparse.Namespace) -> None:
    """Run interactive configuration setup."""
    print_banner()

    # Step 1: Analyze existing configs if available
    print("\n📊 Step 1: Analyzing existing configurations...")
    analyzer = ConfigAnalyzer(args.configs_path)
    patterns = analyzer.analyze()

    if patterns:
        print(f"   ✓ Found {len(patterns.get('configs', []))} existing configs")
        print(f"   ✓ Extracted {len(patterns.get('commands', []))} command patterns")
        print(f"   ✓ Extracted {len(patterns.get('agents', []))} agent patterns")
    else:
        print("   ℹ No existing configs found, starting fresh")

    # Step 2: Research best practices
    print("\n🔍 Step 2: Researching latest best practices...")
    researcher = BestPracticesResearcher()

    if args.skip_research:
        print("   ⏭ Skipping research (--skip-research flag)")
        research_results = None
    else:
        research_results = researcher.research_all()
        print(f"   ✓ Gathered {len(research_results.get('sources', []))} sources")

    # Step 3: Interactive questionnaire
    print("\n❓ Step 3: Configuration questionnaire...")
    engine = QuestionEngine(patterns, research_results)
    answers = engine.run_questionnaire()

    if not answers:
        print("\n❌ Setup cancelled.")
        return

    # Step 4: Generate configuration
    print("\n🔧 Step 4: Generating configuration...")
    generator = ConfigGenerator(patterns, research_results)
    config = generator.generate(answers)

    # Step 5: Multi-model review
    if not args.skip_review:
        print("\n🔬 Step 5: Multi-model review...")
        reviewer = ConfigReviewer()
        review_results = reviewer.review(config)

        if review_results.get("issues"):
            print(f"\n⚠️  Found {len(review_results['issues'])} suggestions:")
            for issue in review_results["issues"][:5]:
                print(f"   • {issue['severity']}: {issue['message']}")

            apply = input("\nApply suggested improvements? [Y/n]: ").strip().lower()
            if apply != 'n':
                config = generator.apply_improvements(config, review_results)
                print("   ✓ Improvements applied")
    else:
        print("\n⏭ Skipping review (--skip-review flag)")

    # Step 6: Write configuration
    print("\n💾 Step 6: Writing configuration...")
    output_path = Path(args.output) if args.output else Path.cwd() / answers.get("config_name", "new-config")
    generator.write_config(config, output_path)

    print(f"\n✅ Configuration created at: {output_path}")
    print("\nNext steps:")
    print(f"   1. Review the generated files in {output_path}")
    print(f"   2. Copy to your project: cp -r {output_path}/.claude your-project/")
    print(f"   3. Customize CLAUDE.md for your specific needs")


def run_analyze(args: argparse.Namespace) -> None:
    """Analyze existing configurations."""
    print("📊 Analyzing configurations...\n")

    analyzer = ConfigAnalyzer(args.configs_path)
    patterns = analyzer.analyze()

    if args.json:
        import json
        print(json.dumps(patterns, indent=2))
    else:
        analyzer.print_summary(patterns)


def run_research(args: argparse.Namespace) -> None:
    """Research Claude Code best practices."""
    print("🔍 Researching best practices...\n")

    researcher = BestPracticesResearcher()

    if args.topic:
        results = researcher.research_topic(args.topic)
    else:
        results = researcher.research_all()

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        researcher.print_summary(results)


def run_review(args: argparse.Namespace) -> None:
    """Review an existing configuration."""
    print("🔬 Reviewing configuration...\n")

    config_path = Path(args.config_path)
    if not config_path.exists():
        print(f"❌ Config not found: {config_path}")
        sys.exit(1)

    reviewer = ConfigReviewer()
    results = reviewer.review_path(config_path)

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        reviewer.print_results(results)


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Config Setup Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Interactive setup
  %(prog)s --quick                  # Quick setup with defaults
  %(prog)s analyze                  # Analyze existing configs
  %(prog)s research                 # Research best practices
  %(prog)s review ./my-config       # Review a config
        """
    )

    parser.add_argument(
        "--configs-path",
        default=str(Path.home() / "claude-configs"),
        help="Path to existing configs directory"
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
        "--quick",
        action="store_true",
        help="Quick mode with sensible defaults"
    )

    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze existing configs")
    analyze_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Research subcommand
    research_parser = subparsers.add_parser("research", help="Research best practices")
    research_parser.add_argument("--topic", help="Specific topic to research")
    research_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Review subcommand
    review_parser = subparsers.add_parser("review", help="Review a configuration")
    review_parser.add_argument("config_path", help="Path to config to review")
    review_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "analyze":
        run_analyze(args)
    elif args.command == "research":
        run_research(args)
    elif args.command == "review":
        run_review(args)
    else:
        run_interactive(args)


if __name__ == "__main__":
    main()
