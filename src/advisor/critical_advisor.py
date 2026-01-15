#!/usr/bin/env python3
"""
Critical Advisor - Questions assumptions and provides thoughtful feedback.

This module:
- Challenges user choices that may be suboptimal
- Identifies potential issues before they become problems
- Suggests alternatives based on best practices
- Validates configuration choices against research
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Concern:
    """A concern or question about a user's choice."""
    severity: str  # critical, warning, suggestion
    category: str
    message: str
    question: str
    recommendation: str
    context: str = ""


@dataclass
class ValidationResult:
    """Result of validating user choices."""
    is_valid: bool
    concerns: list[Concern]
    score: int  # 0-100 confidence score
    summary: str


class CriticalAdvisor:
    """Critically analyzes user choices and configurations."""

    def __init__(self, research_results: Optional[dict] = None):
        self.research_results = research_results or {}
        self.concerns: list[Concern] = []

    def analyze_choices(self, answers: dict) -> ValidationResult:
        """Analyze user choices and identify potential issues."""
        self.concerns = []

        # Check for common anti-patterns
        self._check_security_choices(answers)
        self._check_autonomy_choices(answers)
        self._check_feature_coherence(answers)
        self._check_tech_stack_alignment(answers)
        self._check_missing_essentials(answers)

        # Calculate overall score
        score = self._calculate_score()

        # Build summary
        critical_count = len([c for c in self.concerns if c.severity == "critical"])
        warning_count = len([c for c in self.concerns if c.severity == "warning"])

        if critical_count > 0:
            summary = f"Found {critical_count} critical issue(s) that should be addressed"
        elif warning_count > 2:
            summary = f"Found {warning_count} warnings - configuration may need adjustment"
        elif self.concerns:
            summary = "Minor suggestions available for optimization"
        else:
            summary = "Configuration looks solid!"

        return ValidationResult(
            is_valid=critical_count == 0,
            concerns=self.concerns,
            score=score,
            summary=summary
        )

    def _check_security_choices(self, answers: dict) -> None:
        """Check security-related choices."""
        security_level = answers.get("security_level", "")
        allow_deletion = answers.get("allow_file_deletion", "")
        autonomy = answers.get("autonomy_level", "")
        purpose = answers.get("purpose", "")

        # High autonomy + relaxed security = risky
        if "Co-founder" in autonomy and "Relaxed" in security_level:
            self.concerns.append(Concern(
                severity="warning",
                category="security",
                message="High autonomy with relaxed security may be risky",
                question="Are you sure you want Claude to operate with minimal restrictions?",
                recommendation="Consider 'Standard' security for co-founder mode to prevent accidental damage",
                context="Co-founder mode gives Claude significant freedom. Pairing this with relaxed security removes most safeguards."
            ))

        # Enterprise purpose but not high security
        if "Enterprise" in purpose and "Maximum" not in security_level and "High" not in security_level:
            self.concerns.append(Concern(
                severity="critical",
                category="security",
                message="Enterprise use case requires higher security level",
                question="Is this configuration for production systems?",
                recommendation="Switch to 'High' or 'Maximum' security for enterprise deployments",
                context="Enterprise systems typically require stricter controls to meet compliance requirements."
            ))

        # Allowing full deletion for enterprise
        if "Enterprise" in purpose and "Yes" in allow_deletion:
            self.concerns.append(Concern(
                severity="warning",
                category="security",
                message="Unrestricted file deletion in enterprise context",
                question="Should Claude be able to delete any file?",
                recommendation="Use 'Limited - Only files it created' for enterprise deployments",
                context="Unrestricted deletion can cause significant issues in production environments."
            ))

        # No secrets configured but secrets location specified
        has_secrets = answers.get("has_secrets", False)
        secrets_location = answers.get("secrets_location", "")
        if not has_secrets and secrets_location:
            self.concerns.append(Concern(
                severity="suggestion",
                category="security",
                message="Secrets location specified but secrets not enabled",
                question="Do you plan to use API keys or secrets?",
                recommendation="Enable secrets management for multi-model features",
                context="Many advanced features require API keys."
            ))

    def _check_autonomy_choices(self, answers: dict) -> None:
        """Check autonomy and workflow choices."""
        autonomy = answers.get("autonomy_level", "")
        purpose = answers.get("purpose", "")
        enable_memory = answers.get("enable_memory", False)

        # Co-founder mode without memory system
        if "Co-founder" in autonomy and not enable_memory:
            self.concerns.append(Concern(
                severity="warning",
                category="workflow",
                message="Co-founder mode works best with memory system",
                question="Should Claude remember context across sessions?",
                recommendation="Enable memory system for co-founder mode to maintain continuity",
                context="Co-founders need to remember decisions, mistakes, and context to be effective."
            ))

        # Learning purpose but assistant autonomy
        if "Learning" in purpose and "Assistant" in autonomy:
            self.concerns.append(Concern(
                severity="suggestion",
                category="workflow",
                message="Learning mode may benefit from more autonomy",
                question="Do you want Claude to guide your learning proactively?",
                recommendation="Consider 'Senior dev' autonomy for more educational interactions",
                context="Higher autonomy allows Claude to point out learning opportunities."
            ))

        # Solo dev with low autonomy
        if "Solo" in purpose and "Assistant" in autonomy:
            self.concerns.append(Concern(
                severity="suggestion",
                category="workflow",
                message="Solo developers often benefit from higher autonomy",
                question="Do you want to spend less time directing Claude?",
                recommendation="Consider 'Co-founder' or 'Senior dev' for solo projects",
                context="Without a team to review, autonomous Claude can iterate faster."
            ))

    def _check_feature_coherence(self, answers: dict) -> None:
        """Check that enabled features make sense together."""
        enable_multi_model = answers.get("enable_multi_model", False)
        enable_hooks = answers.get("enable_hooks", [])
        enable_agents = answers.get("enable_agents", [])
        enable_commands = answers.get("enable_commands", [])

        # Multi-model without review command
        if enable_multi_model:
            review_commands = [c for c in enable_commands if "review" in c.lower()]
            if not review_commands:
                self.concerns.append(Concern(
                    severity="suggestion",
                    category="features",
                    message="Multi-model enabled but no review command",
                    question="How will you trigger multi-model reviews?",
                    recommendation="Add '/review' command to easily invoke multi-model reviews",
                    context="Multi-model review is most useful when easily accessible via command."
                ))

        # Code reviewer agent without review workflow
        code_reviewer = any("Code Reviewer" in a for a in enable_agents)
        if code_reviewer and not enable_multi_model:
            self.concerns.append(Concern(
                severity="suggestion",
                category="features",
                message="Code reviewer agent without multi-model review",
                question="Would you like multiple perspectives on code reviews?",
                recommendation="Enable multi-model review for more comprehensive code analysis",
                context="Multiple models catch different types of issues."
            ))

        # Metrics tracking without hooks
        if enable_agents and not enable_hooks:
            self.concerns.append(Concern(
                severity="suggestion",
                category="features",
                message="Agents enabled but no hooks configured",
                question="Would automated triggers improve your workflow?",
                recommendation="Consider enabling hooks for automatic quality checks",
                context="Hooks can trigger agents automatically at the right moments."
            ))

    def _check_tech_stack_alignment(self, answers: dict) -> None:
        """Check that tech stack choices align with other settings."""
        language = answers.get("primary_language", "")
        frameworks = answers.get("frameworks", [])
        package_manager = answers.get("package_manager", "")
        test_runner = answers.get("test_runner", "")

        # Python with npm
        if "Python" in language and package_manager in ["npm", "pnpm", "yarn"]:
            self.concerns.append(Concern(
                severity="warning",
                category="tech_stack",
                message="Python language with JavaScript package manager",
                question="Is your project actually a polyglot project?",
                recommendation="Use pip/poetry for Python projects, or select 'Multiple languages'",
                context="Mismatched tools can cause confusion in generated commands."
            ))

        # JavaScript without jest/vitest
        if language in ["TypeScript/JavaScript"] and test_runner in ["pytest", "go test"]:
            self.concerns.append(Concern(
                severity="warning",
                category="tech_stack",
                message="JavaScript project with non-JavaScript test runner",
                question="What test framework do you actually use?",
                recommendation="Consider jest or vitest for JavaScript/TypeScript projects",
                context="Test runner should match your actual project setup."
            ))

        # React without Next.js awareness
        if any("React" in f for f in frameworks) and not any("Next" in f for f in frameworks):
            # Just a suggestion, not a concern
            pass

    def _check_missing_essentials(self, answers: dict) -> None:
        """Check for missing essential configurations."""
        enable_commands = answers.get("enable_commands", [])
        enable_agents = answers.get("enable_agents", [])
        enable_memory = answers.get("enable_memory", False)
        security_level = answers.get("security_level", "")

        # No reflect command but memory enabled
        has_reflect = any("reflect" in c.lower() for c in enable_commands)
        if enable_memory and not has_reflect:
            self.concerns.append(Concern(
                severity="suggestion",
                category="essentials",
                message="Memory system without reflection capability",
                question="How will Claude learn from mistakes?",
                recommendation="Add '/reflect' command to enable learning from errors",
                context="Reflection is key to improving the memory system's value."
            ))

        # High security but no security auditor
        has_security_auditor = any("Security" in a for a in enable_agents)
        if "High" in security_level or "Maximum" in security_level:
            if not has_security_auditor:
                self.concerns.append(Concern(
                    severity="suggestion",
                    category="essentials",
                    message="High security level without security auditor agent",
                    question="Would automated security scanning help?",
                    recommendation="Enable Security Auditor agent for proactive vulnerability detection",
                    context="Security auditor can catch issues before they reach production."
                ))

        # No commands at all
        if not enable_commands:
            self.concerns.append(Concern(
                severity="suggestion",
                category="essentials",
                message="No slash commands configured",
                question="Would quick commands improve your workflow?",
                recommendation="Consider adding at least /review and /reflect commands",
                context="Commands provide quick access to common operations."
            ))

    def _calculate_score(self) -> int:
        """Calculate an overall confidence score (0-100)."""
        base_score = 100

        for concern in self.concerns:
            if concern.severity == "critical":
                base_score -= 25
            elif concern.severity == "warning":
                base_score -= 10
            elif concern.severity == "suggestion":
                base_score -= 3

        return max(0, min(100, base_score))

    def present_concerns(self) -> bool:
        """Present concerns to user and allow them to address them.

        Returns True if user wants to continue, False to go back.
        """
        if not self.concerns:
            print("\n✅ Your configuration looks great! No concerns identified.")
            return True

        critical = [c for c in self.concerns if c.severity == "critical"]
        warnings = [c for c in self.concerns if c.severity == "warning"]
        suggestions = [c for c in self.concerns if c.severity == "suggestion"]

        print("\n" + "=" * 60)
        print("🤔 CONFIGURATION REVIEW")
        print("=" * 60)

        if critical:
            print("\n❌ CRITICAL ISSUES (should fix)")
            for c in critical:
                print(f"\n   {c.message}")
                print(f"   → {c.question}")
                print(f"   💡 {c.recommendation}")

        if warnings:
            print("\n⚠️  WARNINGS (consider addressing)")
            for c in warnings:
                print(f"\n   {c.message}")
                print(f"   → {c.question}")
                print(f"   💡 {c.recommendation}")

        if suggestions:
            print("\n💡 SUGGESTIONS (optional improvements)")
            for c in suggestions[:3]:  # Limit to top 3
                print(f"\n   {c.message}")
                print(f"   💡 {c.recommendation}")

        print("\n" + "-" * 60)

        if critical:
            print("\n⚠️  Critical issues found. Strongly recommend addressing them.")
            choice = input("Continue anyway? [y/N]: ").strip().lower()
            return choice == 'y'
        else:
            choice = input("\nProceed with current configuration? [Y/n]: ").strip().lower()
            return choice != 'n'

    def get_improvements(self, answers: dict) -> dict:
        """Suggest specific improvements to the answers."""
        improvements = {}

        for concern in self.concerns:
            if concern.severity == "critical":
                # Auto-suggest fixes for critical issues
                if "security" in concern.category and "Enterprise" in answers.get("purpose", ""):
                    improvements["security_level"] = "High - Production systems"

        return improvements
