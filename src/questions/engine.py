#!/usr/bin/env python3
"""
Question Engine - Interactive questionnaire for config generation.

Asks targeted questions to understand the user's needs and generates
appropriate configuration based on their answers.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from enum import Enum


class QuestionType(Enum):
    TEXT = "text"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    CONFIRM = "confirm"
    NUMBER = "number"


@dataclass
class Question:
    """A single question in the questionnaire."""
    key: str
    prompt: str
    type: QuestionType
    options: list[str] = field(default_factory=list)
    default: Any = None
    required: bool = True
    help_text: str = ""
    condition: Optional[Callable[[dict], bool]] = None  # Show only if condition is met
    validator: Optional[Callable[[Any], bool]] = None


@dataclass
class QuestionGroup:
    """A group of related questions."""
    name: str
    description: str
    questions: list[Question]
    emoji: str = "❓"


class QuestionEngine:
    """Interactive questionnaire engine."""

    def __init__(self, existing_patterns: Optional[dict] = None, research_results: Optional[dict] = None):
        self.existing_patterns = existing_patterns or {}
        self.research_results = research_results or {}
        self.answers: dict[str, Any] = {}
        self.groups = self._build_question_groups()

    def _build_question_groups(self) -> list[QuestionGroup]:
        """Build the complete questionnaire."""
        return [
            self._build_basics_group(),
            self._build_tech_stack_group(),
            self._build_workflow_group(),
            self._build_security_group(),
            self._build_features_group(),
            self._build_multi_model_group(),
        ]

    def _build_basics_group(self) -> QuestionGroup:
        """Basic configuration questions."""
        return QuestionGroup(
            name="Basics",
            description="Let's start with the fundamentals",
            emoji="📋",
            questions=[
                Question(
                    key="config_name",
                    prompt="What should we call this configuration?",
                    type=QuestionType.TEXT,
                    default="my-claude-config",
                    help_text="This will be the directory name (e.g., 'cofounder-v1', 'dev-config')"
                ),
                Question(
                    key="identity",
                    prompt="How should Claude address you?",
                    type=QuestionType.TEXT,
                    default="Boss",
                    help_text="Claude will use this name to confirm it read your config"
                ),
                Question(
                    key="purpose",
                    prompt="What is the primary purpose of this config?",
                    type=QuestionType.SELECT,
                    options=[
                        "Solo development - personal projects",
                        "Team collaboration - shared codebase",
                        "Learning - educational and practice",
                        "Enterprise - production systems",
                        "Research - experimental and prototyping",
                        "Custom - I'll specify below"
                    ],
                    default="Solo development - personal projects"
                ),
                Question(
                    key="purpose_custom",
                    prompt="Describe your custom purpose:",
                    type=QuestionType.TEXT,
                    required=False,
                    condition=lambda a: a.get("purpose", "").startswith("Custom")
                ),
            ]
        )

    def _build_tech_stack_group(self) -> QuestionGroup:
        """Tech stack questions."""
        return QuestionGroup(
            name="Tech Stack",
            description="Tell me about your development environment",
            emoji="🛠️",
            questions=[
                Question(
                    key="primary_language",
                    prompt="What's your primary programming language?",
                    type=QuestionType.SELECT,
                    options=[
                        "Python",
                        "TypeScript/JavaScript",
                        "Go",
                        "Rust",
                        "Java/Kotlin",
                        "C/C++",
                        "Ruby",
                        "Multiple languages"
                    ],
                    default="Python"
                ),
                Question(
                    key="frameworks",
                    prompt="What frameworks do you use?",
                    type=QuestionType.MULTI_SELECT,
                    options=[
                        "React/Next.js",
                        "Vue/Nuxt",
                        "FastAPI",
                        "Django",
                        "Flask",
                        "Express/Node",
                        "Spring Boot",
                        "Rails",
                        "None/Vanilla"
                    ],
                    help_text="Select all that apply"
                ),
                Question(
                    key="package_manager",
                    prompt="What package manager do you use?",
                    type=QuestionType.SELECT,
                    options=[
                        "npm",
                        "pnpm",
                        "yarn",
                        "pip/poetry",
                        "cargo",
                        "go modules",
                        "maven/gradle",
                        "bundler"
                    ],
                    default="pip/poetry"
                ),
                Question(
                    key="database",
                    prompt="What database(s) do you use?",
                    type=QuestionType.MULTI_SELECT,
                    options=[
                        "PostgreSQL",
                        "MySQL",
                        "SQLite",
                        "MongoDB",
                        "Redis",
                        "DynamoDB",
                        "Firestore",
                        "None"
                    ]
                ),
            ]
        )

    def _build_workflow_group(self) -> QuestionGroup:
        """Workflow and commands questions."""
        return QuestionGroup(
            name="Workflow",
            description="How do you work with Claude?",
            emoji="⚡",
            questions=[
                Question(
                    key="autonomy_level",
                    prompt="How autonomous should Claude be?",
                    type=QuestionType.SELECT,
                    options=[
                        "Co-founder - Highly autonomous, proactive",
                        "Senior dev - Autonomous with check-ins",
                        "Junior dev - Guided, asks questions",
                        "Assistant - Waits for instructions"
                    ],
                    default="Co-founder - Highly autonomous, proactive",
                    help_text="Higher autonomy = less interruptions but more trust needed"
                ),
                Question(
                    key="common_tasks",
                    prompt="What tasks do you do most often?",
                    type=QuestionType.MULTI_SELECT,
                    options=[
                        "Code review",
                        "Bug fixing",
                        "New feature development",
                        "Refactoring",
                        "Testing/TDD",
                        "Documentation",
                        "DevOps/CI-CD",
                        "Research"
                    ]
                ),
                Question(
                    key="test_runner",
                    prompt="What test runner do you use?",
                    type=QuestionType.SELECT,
                    options=[
                        "pytest",
                        "jest",
                        "vitest",
                        "go test",
                        "cargo test",
                        "JUnit",
                        "RSpec",
                        "Custom/None"
                    ],
                    default="pytest"
                ),
                Question(
                    key="build_command",
                    prompt="What's your build command?",
                    type=QuestionType.TEXT,
                    default="npm run build",
                    help_text="e.g., 'npm run build', 'make', 'cargo build'"
                ),
            ]
        )

    def _build_security_group(self) -> QuestionGroup:
        """Security and permissions questions."""
        return QuestionGroup(
            name="Security",
            description="Configure safety and permissions",
            emoji="🔒",
            questions=[
                Question(
                    key="security_level",
                    prompt="What security level do you need?",
                    type=QuestionType.SELECT,
                    options=[
                        "Maximum - Enterprise, restricted",
                        "High - Production systems",
                        "Standard - General development",
                        "Relaxed - Personal projects, trust Claude"
                    ],
                    default="Standard - General development"
                ),
                Question(
                    key="allow_file_deletion",
                    prompt="Allow Claude to delete files?",
                    type=QuestionType.SELECT,
                    options=[
                        "Yes - Trust Claude's judgment",
                        "Limited - Only files it created",
                        "No - Never delete without asking"
                    ],
                    default="Limited - Only files it created"
                ),
                Question(
                    key="allow_shell_commands",
                    prompt="What shell commands should Claude run freely?",
                    type=QuestionType.MULTI_SELECT,
                    options=[
                        "git operations",
                        "package managers (npm, pip, etc.)",
                        "build tools",
                        "test runners",
                        "linters",
                        "docker commands",
                        "cloud CLI (aws, gcloud, etc.)"
                    ],
                    default=["git operations", "package managers (npm, pip, etc.)", "test runners", "linters"]
                ),
                Question(
                    key="has_secrets",
                    prompt="Do you use API keys or secrets?",
                    type=QuestionType.CONFIRM,
                    default=True
                ),
                Question(
                    key="secrets_location",
                    prompt="Where are your secrets stored?",
                    type=QuestionType.TEXT,
                    default="~/.secrets/load.sh",
                    condition=lambda a: a.get("has_secrets", False)
                ),
            ]
        )

    def _build_features_group(self) -> QuestionGroup:
        """Optional features questions."""
        return QuestionGroup(
            name="Features",
            description="Enable optional capabilities",
            emoji="✨",
            questions=[
                Question(
                    key="enable_hooks",
                    prompt="Enable automated hooks?",
                    type=QuestionType.MULTI_SELECT,
                    options=[
                        "Post-edit safety check",
                        "Pre-commit linting",
                        "Session metrics tracking",
                        "Auto-reflection on errors",
                        "Modified file tracking"
                    ],
                    help_text="Hooks run automatically on specific events"
                ),
                Question(
                    key="enable_memory",
                    prompt="Enable persistent memory system?",
                    type=QuestionType.CONFIRM,
                    default=True,
                    help_text="Creates docs/memory/ for context across sessions"
                ),
                Question(
                    key="enable_agents",
                    prompt="Which specialized agents do you want?",
                    type=QuestionType.MULTI_SELECT,
                    options=[
                        "Code Reviewer - Quality & security checks",
                        "Architect - Design decisions",
                        "Researcher - Deep investigations",
                        "Debugger - Error analysis",
                        "Security Auditor - Vulnerability scanning"
                    ]
                ),
                Question(
                    key="enable_commands",
                    prompt="Which slash commands do you want?",
                    type=QuestionType.MULTI_SELECT,
                    options=[
                        "/reflect - Learn from mistakes",
                        "/review - Code review workflow",
                        "/standup - Daily standup summary",
                        "/research - Deep research mode",
                        "/check - Pre-commit checklist"
                    ]
                ),
            ]
        )

    def _build_multi_model_group(self) -> QuestionGroup:
        """Multi-model configuration questions."""
        return QuestionGroup(
            name="Multi-Model",
            description="Configure multi-model review system",
            emoji="🤖",
            questions=[
                Question(
                    key="enable_multi_model",
                    prompt="Enable multi-model code review?",
                    type=QuestionType.CONFIRM,
                    default=True,
                    help_text="Uses GPT-5.2 + Gemini 3 for comprehensive review"
                ),
                Question(
                    key="models_to_enable",
                    prompt="Which models should be enabled?",
                    type=QuestionType.MULTI_SELECT,
                    options=[
                        "OpenAI GPT-5.2 Codex",
                        "Google Gemini 3 Pro",
                        "Anthropic Claude (requires separate key)"
                    ],
                    default=["OpenAI GPT-5.2 Codex", "Google Gemini 3 Pro"],
                    condition=lambda a: a.get("enable_multi_model", False)
                ),
                Question(
                    key="enable_optillm",
                    prompt="Enable OptILLM optimization?",
                    type=QuestionType.CONFIRM,
                    default=False,
                    help_text="Requires optillm server running locally",
                    condition=lambda a: a.get("enable_multi_model", False)
                ),
                Question(
                    key="optillm_technique",
                    prompt="Which OptILLM technique?",
                    type=QuestionType.SELECT,
                    options=[
                        "moa - Mixture of Agents",
                        "cot_reflection - Chain-of-thought with reflection",
                        "mcts - Monte Carlo Tree Search",
                        "self_consistency - Multiple samples voting"
                    ],
                    default="moa - Mixture of Agents",
                    condition=lambda a: a.get("enable_optillm", False)
                ),
            ]
        )

    def _ask_question(self, question: Question) -> Any:
        """Ask a single question and return the answer."""
        # Check condition
        if question.condition and not question.condition(self.answers):
            return question.default

        print(f"\n{question.prompt}")

        if question.help_text:
            print(f"   💡 {question.help_text}")

        if question.type == QuestionType.TEXT:
            default_hint = f" [{question.default}]" if question.default else ""
            answer = input(f"   → {default_hint}: ").strip()
            return answer if answer else question.default

        elif question.type == QuestionType.SELECT:
            for i, opt in enumerate(question.options, 1):
                default_marker = " (default)" if opt == question.default else ""
                print(f"   {i}. {opt}{default_marker}")

            while True:
                choice = input("   → Enter number: ").strip()
                if not choice and question.default:
                    return question.default
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(question.options):
                        return question.options[idx]
                except ValueError:
                    pass
                print("   ⚠️ Invalid choice, try again")

        elif question.type == QuestionType.MULTI_SELECT:
            for i, opt in enumerate(question.options, 1):
                print(f"   {i}. {opt}")

            print("   → Enter numbers separated by commas (e.g., 1,3,5)")
            if question.default:
                print(f"   → Press Enter for defaults: {question.default}")

            choice = input("   → : ").strip()
            if not choice and question.default:
                return question.default

            selected = []
            for num in choice.split(","):
                try:
                    idx = int(num.strip()) - 1
                    if 0 <= idx < len(question.options):
                        selected.append(question.options[idx])
                except ValueError:
                    pass
            return selected if selected else question.default

        elif question.type == QuestionType.CONFIRM:
            default_hint = "Y/n" if question.default else "y/N"
            answer = input(f"   → [{default_hint}]: ").strip().lower()
            if not answer:
                return question.default
            return answer in ("y", "yes", "true", "1")

        elif question.type == QuestionType.NUMBER:
            default_hint = f" [{question.default}]" if question.default else ""
            while True:
                answer = input(f"   → {default_hint}: ").strip()
                if not answer and question.default is not None:
                    return question.default
                try:
                    return int(answer)
                except ValueError:
                    print("   ⚠️ Please enter a number")

        return question.default

    def run_questionnaire(self) -> Optional[dict]:
        """Run the complete questionnaire."""
        print("\n" + "=" * 60)
        print("Let's configure your Claude Code setup!")
        print("Press Ctrl+C at any time to cancel.")
        print("=" * 60)

        try:
            for group in self.groups:
                print(f"\n\n{group.emoji} {group.name.upper()}")
                print(f"   {group.description}")
                print("-" * 40)

                for question in group.questions:
                    answer = self._ask_question(question)
                    self.answers[question.key] = answer

            # Summary
            print("\n\n" + "=" * 60)
            print("📝 CONFIGURATION SUMMARY")
            print("=" * 60)

            self._print_summary()

            confirm = input("\n\nProceed with this configuration? [Y/n]: ").strip().lower()
            if confirm == 'n':
                return None

            return self.answers

        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled.")
            return None

    def _print_summary(self) -> None:
        """Print a summary of the answers."""
        key_items = [
            ("Config Name", self.answers.get("config_name")),
            ("Identity", self.answers.get("identity")),
            ("Purpose", self.answers.get("purpose")),
            ("Language", self.answers.get("primary_language")),
            ("Autonomy", self.answers.get("autonomy_level")),
            ("Security", self.answers.get("security_level")),
            ("Multi-Model", "Yes" if self.answers.get("enable_multi_model") else "No"),
            ("Memory System", "Yes" if self.answers.get("enable_memory") else "No"),
        ]

        for label, value in key_items:
            if value:
                display = value[:40] + "..." if len(str(value)) > 40 else value
                print(f"   {label}: {display}")
