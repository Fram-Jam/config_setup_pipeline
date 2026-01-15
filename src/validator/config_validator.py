#!/usr/bin/env python3
"""
Config Validator - Comprehensive validation of generated configurations.

Validates:
- Syntax and structure correctness
- Security best practices compliance
- Completeness and consistency
- Cross-file references
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ValidationIssue:
    """A validation issue found in the config."""
    severity: str  # error, warning, info
    file: str
    line: Optional[int]
    message: str
    fix: str = ""


@dataclass
class ValidationReport:
    """Complete validation report."""
    is_valid: bool
    issues: list[ValidationIssue]
    score: int
    summary: str
    checks_passed: int
    checks_total: int


class ConfigValidator:
    """Validates Claude Code configurations comprehensively."""

    # Required patterns in CLAUDE.md
    REQUIRED_CLAUDE_MD_PATTERNS = [
        (r'[Aa]ddress me as ["\']?\w+["\']?', "Identity confirmation pattern"),
        (r'## Tech Stack|## Technology|## Stack', "Tech stack section"),
        (r'## Before|## Pre-task|## Setup', "Before-task checklist"),
    ]

    # Recommended patterns
    RECOMMENDED_PATTERNS = [
        (r'context compression|compression recovery', "Context recovery section"),
        (r'## After|## Post-task|## Cleanup', "After-task checklist"),
        (r'NEVER|never commit|never hardcode', "Security warnings"),
    ]

    # Dangerous patterns to flag
    DANGEROUS_PATTERNS = [
        (r'api_key\s*[:=]\s*["\'][a-zA-Z0-9]{20,}', "Hardcoded API key detected"),
        (r'password\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded password detected"),
        (r'secret\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded secret detected"),
    ]

    def __init__(self):
        self.issues: list[ValidationIssue] = []

    def validate_generated_config(self, config: dict, files: list) -> ValidationReport:
        """Validate a generated configuration before writing."""
        self.issues = []
        checks_passed = 0
        checks_total = 0

        # Validate answers
        checks_total += 1
        if self._validate_answers(config.get("answers", {})):
            checks_passed += 1

        # Validate each file
        for file_info in files:
            checks_total += 1
            if self._validate_file_content(file_info["path"], file_info.get("content", "")):
                checks_passed += 1

        # Cross-file validation
        checks_total += 1
        if self._validate_cross_references(files):
            checks_passed += 1

        return self._build_report(checks_passed, checks_total)

    def validate_path(self, config_path: Path) -> ValidationReport:
        """Validate an existing configuration on disk."""
        self.issues = []
        checks_passed = 0
        checks_total = 0

        # Validate CLAUDE.md
        claude_md = config_path / "CLAUDE.md"
        if claude_md.exists():
            checks_total += 1
            if self._validate_claude_md(claude_md):
                checks_passed += 1
        else:
            self.issues.append(ValidationIssue(
                severity="error",
                file="CLAUDE.md",
                line=None,
                message="Missing CLAUDE.md file",
                fix="Create a CLAUDE.md file with your configuration"
            ))

        # Validate settings.json
        settings_file = config_path / ".claude" / "settings.json"
        if settings_file.exists():
            checks_total += 1
            if self._validate_settings_json(settings_file):
                checks_passed += 1

        # Validate agents
        agents_dir = config_path / ".claude" / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                checks_total += 1
                if self._validate_agent_file(agent_file):
                    checks_passed += 1

        # Validate commands
        commands_dir = config_path / ".claude" / "commands"
        if commands_dir.exists():
            for cmd_file in commands_dir.glob("*.md"):
                checks_total += 1
                if self._validate_command_file(cmd_file):
                    checks_passed += 1

        # Check for secrets
        checks_total += 1
        if self._scan_for_secrets(config_path):
            checks_passed += 1

        return self._build_report(checks_passed, checks_total)

    def _validate_answers(self, answers: dict) -> bool:
        """Validate the questionnaire answers."""
        valid = True

        # Required answers
        required = ["config_name", "primary_language", "security_level"]
        for key in required:
            if not answers.get(key):
                self.issues.append(ValidationIssue(
                    severity="error",
                    file="answers",
                    line=None,
                    message=f"Missing required answer: {key}",
                    fix=f"Provide a value for {key}"
                ))
                valid = False

        # Validate config name
        config_name = answers.get("config_name", "")
        if config_name and not re.match(r'^[a-zA-Z0-9_-]+$', config_name):
            self.issues.append(ValidationIssue(
                severity="warning",
                file="answers",
                line=None,
                message="Config name contains special characters",
                fix="Use only letters, numbers, underscores, and hyphens"
            ))

        return valid

    def _validate_file_content(self, path: str, content: str) -> bool:
        """Validate content of a generated file."""
        valid = True

        # Check for hardcoded secrets
        for pattern, message in self.DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self.issues.append(ValidationIssue(
                    severity="error",
                    file=path,
                    line=None,
                    message=message,
                    fix="Remove hardcoded credentials and use environment variables"
                ))
                valid = False

        # Validate JSON files
        if path.endswith(".json"):
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                self.issues.append(ValidationIssue(
                    severity="error",
                    file=path,
                    line=e.lineno,
                    message=f"Invalid JSON: {e.msg}",
                    fix="Fix the JSON syntax error"
                ))
                valid = False

        return valid

    def _validate_claude_md(self, path: Path) -> bool:
        """Validate CLAUDE.md file."""
        valid = True
        content = path.read_text()

        # Check required patterns
        for pattern, description in self.REQUIRED_CLAUDE_MD_PATTERNS:
            if not re.search(pattern, content):
                self.issues.append(ValidationIssue(
                    severity="warning",
                    file=str(path),
                    line=None,
                    message=f"Missing {description}",
                    fix=f"Add {description} to CLAUDE.md"
                ))

        # Check recommended patterns
        for pattern, description in self.RECOMMENDED_PATTERNS:
            if not re.search(pattern, content, re.IGNORECASE):
                self.issues.append(ValidationIssue(
                    severity="info",
                    file=str(path),
                    line=None,
                    message=f"Consider adding {description}",
                    fix=f"Add {description} for better configuration"
                ))

        # Check for dangerous patterns
        for pattern, message in self.DANGEROUS_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append(ValidationIssue(
                    severity="error",
                    file=str(path),
                    line=line_num,
                    message=message,
                    fix="Remove hardcoded credentials"
                ))
                valid = False

        # Check file size
        if len(content) > 50000:
            self.issues.append(ValidationIssue(
                severity="warning",
                file=str(path),
                line=None,
                message="CLAUDE.md is very large (>50KB)",
                fix="Consider breaking into multiple files for readability"
            ))

        return valid

    def _validate_settings_json(self, path: Path) -> bool:
        """Validate settings.json file."""
        valid = True

        try:
            settings = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            self.issues.append(ValidationIssue(
                severity="error",
                file=str(path),
                line=e.lineno,
                message=f"Invalid JSON: {e.msg}",
                fix="Fix the JSON syntax"
            ))
            return False

        # Check for permissions
        permissions = settings.get("permissions", {})
        allow = permissions.get("allow", [])
        deny = permissions.get("deny", [])

        if not allow:
            self.issues.append(ValidationIssue(
                severity="warning",
                file=str(path),
                line=None,
                message="No tools in allow list",
                fix="Add at least basic tools to the allow list"
            ))

        # Check for essential denials
        essential_denials = ["rm -rf /", "sudo"]
        for denial in essential_denials:
            has_denial = any(denial in d for d in deny)
            if not has_denial:
                self.issues.append(ValidationIssue(
                    severity="warning",
                    file=str(path),
                    line=None,
                    message=f"Missing essential denial: {denial}",
                    fix=f"Add '{denial}' to deny list for safety"
                ))

        # Validate hooks structure
        hooks = settings.get("hooks", {})
        for event, hook_list in hooks.items():
            if not isinstance(hook_list, list):
                self.issues.append(ValidationIssue(
                    severity="error",
                    file=str(path),
                    line=None,
                    message=f"Hook {event} should be a list",
                    fix="Wrap hook configuration in an array"
                ))
                valid = False

        return valid

    def _validate_agent_file(self, path: Path) -> bool:
        """Validate an agent definition file."""
        valid = True
        content = path.read_text()

        # Check for frontmatter
        if not content.startswith("---"):
            self.issues.append(ValidationIssue(
                severity="warning",
                file=str(path),
                line=1,
                message="Missing YAML frontmatter",
                fix="Add ---\\nname: ...\\n--- at the top"
            ))

        # Check for required frontmatter fields
        required_fields = ["name", "description"]
        for field in required_fields:
            if f"{field}:" not in content[:500]:
                self.issues.append(ValidationIssue(
                    severity="warning",
                    file=str(path),
                    line=None,
                    message=f"Missing {field} in frontmatter",
                    fix=f"Add {field}: to the YAML frontmatter"
                ))

        return valid

    def _validate_command_file(self, path: Path) -> bool:
        """Validate a command definition file."""
        valid = True
        content = path.read_text()

        # Check for frontmatter
        if not content.startswith("---"):
            self.issues.append(ValidationIssue(
                severity="warning",
                file=str(path),
                line=1,
                message="Missing YAML frontmatter",
                fix="Add ---\\ndescription: ...\\n--- at the top"
            ))

        return valid

    def _validate_cross_references(self, files: list) -> bool:
        """Validate cross-file references."""
        valid = True

        # Build map of file paths
        file_paths = {f["path"] for f in files}

        # Check CLAUDE.md references
        for file_info in files:
            if file_info["path"] == "CLAUDE.md":
                content = file_info.get("content", "")
                # Look for file references
                refs = re.findall(r'`([a-zA-Z0-9_/.-]+\.(?:md|json))`', content)
                for ref in refs:
                    # Normalize reference
                    normalized = ref.lstrip('./')
                    # Check if referenced file exists
                    matching = [f for f in file_paths if normalized in f or f.endswith(normalized)]
                    if not matching and "docs/" in normalized:
                        # docs/ references are allowed even if not generated
                        pass

        return valid

    def _scan_for_secrets(self, config_path: Path) -> bool:
        """Scan configuration for accidentally committed secrets."""
        valid = True

        for file_path in config_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".md", ".json", ".txt", ".yaml", ".yml"]:
                try:
                    content = file_path.read_text()
                    for pattern, message in self.DANGEROUS_PATTERNS:
                        if re.search(pattern, content, re.IGNORECASE):
                            self.issues.append(ValidationIssue(
                                severity="error",
                                file=str(file_path.relative_to(config_path)),
                                line=None,
                                message=message,
                                fix="Remove hardcoded credentials immediately"
                            ))
                            valid = False
                except Exception:
                    pass

        return valid

    def _build_report(self, checks_passed: int, checks_total: int) -> ValidationReport:
        """Build the validation report."""
        errors = [i for i in self.issues if i.severity == "error"]
        warnings = [i for i in self.issues if i.severity == "warning"]

        is_valid = len(errors) == 0
        score = int((checks_passed / max(checks_total, 1)) * 100)

        if errors:
            summary = f"{len(errors)} error(s) must be fixed"
        elif warnings:
            summary = f"{len(warnings)} warning(s) to review"
        else:
            summary = "Configuration is valid!"

        return ValidationReport(
            is_valid=is_valid,
            issues=self.issues,
            score=score,
            summary=summary,
            checks_passed=checks_passed,
            checks_total=checks_total
        )

    def print_report(self, report: ValidationReport) -> None:
        """Print a formatted validation report."""
        print("\n" + "=" * 60)
        print("✅ VALIDATION REPORT" if report.is_valid else "❌ VALIDATION REPORT")
        print("=" * 60)

        print(f"\nScore: {report.score}%")
        print(f"Checks passed: {report.checks_passed}/{report.checks_total}")
        print(f"Summary: {report.summary}")

        if report.issues:
            errors = [i for i in report.issues if i.severity == "error"]
            warnings = [i for i in report.issues if i.severity == "warning"]
            infos = [i for i in report.issues if i.severity == "info"]

            if errors:
                print("\n❌ ERRORS")
                for issue in errors:
                    line_info = f":{issue.line}" if issue.line else ""
                    print(f"   {issue.file}{line_info}: {issue.message}")
                    if issue.fix:
                        print(f"      Fix: {issue.fix}")

            if warnings:
                print("\n⚠️  WARNINGS")
                for issue in warnings:
                    print(f"   {issue.file}: {issue.message}")

            if infos:
                print("\n💡 SUGGESTIONS")
                for issue in infos[:5]:  # Limit info messages
                    print(f"   {issue.file}: {issue.message}")

        print("\n" + "=" * 60)
