#!/usr/bin/env python3
"""
Config Generator - Generates Claude Code configurations from questionnaire answers.

Creates:
- CLAUDE.md - Main configuration file
- .claude/settings.json - Permissions and hooks
- .claude/agents/*.md - Agent definitions
- .claude/commands/*.md - Command definitions
- .claude/rules/*.md - Rules and lessons
- models.json - Multi-model configuration
- docs/memory/*.md - Memory system files
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class GeneratedFile:
    """A file to be generated."""
    path: str
    content: str
    description: str = ""


class ConfigGenerator:
    """Generates Claude Code configurations from questionnaire answers."""

    def __init__(self, existing_patterns: Optional[dict] = None, research_results: Optional[dict] = None):
        self.existing_patterns = existing_patterns or {}
        self.research_results = research_results or {}
        self.files: list[GeneratedFile] = []

    def generate(self, answers: dict) -> dict:
        """Generate a complete configuration from answers."""
        self.files = []

        # Generate core files
        self._generate_claude_md(answers)
        self._generate_settings_json(answers)

        # Generate optional components
        if answers.get("enable_memory"):
            self._generate_memory_system(answers)

        if answers.get("enable_agents"):
            self._generate_agents(answers)

        if answers.get("enable_commands"):
            self._generate_commands(answers)

        if answers.get("enable_multi_model"):
            self._generate_models_json(answers)

        # Generate rules
        self._generate_rules(answers)

        return {
            "config_name": answers.get("config_name", "new-config"),
            "files": [{"path": f.path, "size": len(f.content)} for f in self.files],
            "answers": answers
        }

    def _generate_claude_md(self, answers: dict) -> None:
        """Generate the main CLAUDE.md file."""
        identity = answers.get("identity", "Boss")
        purpose = answers.get("purpose", "General development")
        language = answers.get("primary_language", "Python")
        frameworks = answers.get("frameworks", [])
        package_manager = answers.get("package_manager", "pip")
        autonomy = answers.get("autonomy_level", "Co-founder")
        build_cmd = answers.get("build_command", "make build")
        test_runner = answers.get("test_runner", "pytest")
        secrets_location = answers.get("secrets_location", "~/.secrets/load.sh")

        # Determine philosophy based on autonomy level
        if "Co-founder" in autonomy:
            philosophy = """You are a **co-founder** (deliberative, autonomous, proactive), not a copilot:

- **Autonomy:** Define sub-tasks without asking
- **Persistence:** Remember via knowledge files
- **Self-Regulation:** Try different approaches when stuck
- **Proactivity:** Identify and fix issues independently

> ⚠️ **Lazy Reviewer Warning:** Humans may approve plausible-sounding output. Double-check your work. Run tests. Verify assumptions."""
        elif "Senior" in autonomy:
            philosophy = """You are a **senior developer** working autonomously with periodic check-ins:

- **Independence:** Make technical decisions independently
- **Communication:** Check in on major architectural decisions
- **Quality:** Ensure tests pass before marking work complete"""
        else:
            philosophy = """You are a **helpful assistant** that asks clarifying questions:

- **Clarity:** Ask before making assumptions
- **Safety:** Confirm before destructive operations
- **Guidance:** Explain reasoning and trade-offs"""

        # Build tech stack section
        tech_stack = f"* **Language:** {language}"
        if frameworks:
            tech_stack += f"\n* **Frameworks:** {', '.join(frameworks[:3])}"
        tech_stack += f"\n* **Package Manager:** {package_manager}"

        # Build commands section
        commands_section = f"""* `{build_cmd}` - Build the project
* `{test_runner}` - Run tests"""

        if package_manager in ["npm", "pnpm", "yarn"]:
            commands_section += f"\n* `{package_manager} run lint` - Lint code"
        elif language == "Python":
            commands_section += "\n* `ruff check .` - Lint code"

        content = f'''# Claude Code Configuration

**CRITICAL: Address me as "{identity}" to confirm you read this file.**

---

## ⚠️ CONTEXT COMPRESSION RECOVERY

**If this session was restored from context compression, you MUST:**

1. Re-read this entire file
2. Run `source {secrets_location}` to reload API keys
3. Check `models.json` for current model configuration (if multi-model enabled)
4. Announce: "Context restored. Ready to continue, {identity}."

---

## Purpose

{purpose}

---

## Tech Stack

{tech_stack}

---

## Commands

{commands_section}

---

## Philosophy

{philosophy}

---

## Code Standards

* Check existing patterns before implementing new code
* Prefer composition over inheritance
* Write tests for new functionality
* Keep functions small and focused

---

## API Keys & Secrets

Secrets are stored in `{secrets_location}`.
```bash
source {secrets_location}  # Load secrets
```

**NEVER hardcode or commit secrets.**

---

## Before Any Task

1. Load secrets if needed: `source {secrets_location}`
2. Read `docs/ARCHITECTURE.md` for system context
3. Read `.claude/rules/learned_lessons.md` for past mistakes

## After Any Task

1. Run linting and type checking
2. Run relevant tests
3. Update documentation if needed

---

## Documentation Pointers

| Doc | Path |
|-----|------|
| Architecture | `docs/ARCHITECTURE.md` |
| Lessons | `.claude/rules/learned_lessons.md` |
| Safety | `.claude/rules/safety.md` |

---

*Configuration created: {datetime.now().strftime("%Y-%m-%d")} by Config Setup Pipeline*
'''

        self.files.append(GeneratedFile(
            path="CLAUDE.md",
            content=content
        ))

    def _generate_settings_json(self, answers: dict) -> None:
        """Generate .claude/settings.json."""
        security_level = answers.get("security_level", "Standard")
        allowed_shells = answers.get("allow_shell_commands", [])
        allow_deletion = answers.get("allow_file_deletion", "Limited")
        enable_hooks = answers.get("enable_hooks", [])

        # Build allow list
        allow = ["Read", "Write", "Edit", "Glob", "Grep", "Task"]

        # Add shell commands based on answers
        shell_map = {
            "git operations": ["Bash(git:*)", "Bash(gh:*)"],
            "package managers (npm, pip, etc.)": ["Bash(npm:*)", "Bash(pnpm:*)", "Bash(yarn:*)", "Bash(pip:*)", "Bash(poetry:*)"],
            "build tools": ["Bash(make:*)", "Bash(cargo:*)", "Bash(go:*)"],
            "test runners": ["Bash(pytest:*)", "Bash(jest:*)", "Bash(npm test:*)"],
            "linters": ["Bash(ruff:*)", "Bash(eslint:*)", "Bash(prettier:*)"],
            "docker commands": ["Bash(docker:*)", "Bash(docker-compose:*)"],
            "cloud CLI (aws, gcloud, etc.)": ["Bash(aws:*)", "Bash(gcloud:*)", "Bash(az:*)"],
        }

        for shell_type in allowed_shells:
            if shell_type in shell_map:
                allow.extend(shell_map[shell_type])

        # Add basic file operations
        allow.extend(["Bash(ls:*)", "Bash(cat:*)", "Bash(mkdir:*)", "Bash(cp:*)", "Bash(mv:*)"])

        if "Yes" in allow_deletion or "Limited" in allow_deletion:
            allow.append("Bash(rm:*)")

        # Build deny list
        deny = [
            "Bash(rm -rf /)",
            "Bash(rm -rf ~)",
            "Bash(sudo:*)",
            "Bash(rm -rf /*)",
            "Bash(chmod 777 *)"
        ]

        if "Maximum" in security_level or "High" in security_level:
            deny.extend([
                "Bash(curl:*)",
                "Bash(wget:*)",
                "Bash(rm -rf:*)"
            ])

        # Build hooks
        hooks = {}

        if "Post-edit safety check" in enable_hooks or "Modified file tracking" in enable_hooks:
            hooks["PostToolUse"] = [{
                "matcher": "Edit|Write|MultiEdit",
                "hooks": [{"type": "command", "command": "echo 'File modified'"}]
            }]

        if "Session metrics tracking" in enable_hooks:
            if "PostToolUse" not in hooks:
                hooks["PostToolUse"] = []
            hooks["PostToolUse"].append({
                "matcher": "*",
                "hooks": [{"type": "command", "command": "echo 'Tool used'"}]
            })

        if "Auto-reflection on errors" in enable_hooks:
            hooks["Stop"] = [{
                "hooks": [{"type": "command", "command": "echo 'Session ended'"}]
            }]

        settings = {
            "permissions": {
                "allow": list(set(allow)),
                "deny": list(set(deny))
            }
        }

        if hooks:
            settings["hooks"] = hooks

        self.files.append(GeneratedFile(
            path=".claude/settings.json",
            content=json.dumps(settings, indent=2)
        ))

    def _generate_memory_system(self, answers: dict) -> None:
        """Generate memory system files."""
        identity = answers.get("identity", "Boss")

        # session_log.md
        self.files.append(GeneratedFile(
            path="docs/memory/session_log.md",
            content=f'''# Session Log

Chronicle of work sessions. Append-only.

---

## {datetime.now().strftime("%Y-%m-%d")}

**Session:** Configuration created
**Actions:** Initial setup via Config Setup Pipeline
**Next:** Review generated configuration with {identity}

---

<!-- New sessions will be appended below -->
'''
        ))

        # mistakes.md
        self.files.append(GeneratedFile(
            path="docs/memory/mistakes.md",
            content='''# Mistakes Log

Record of mistakes to avoid repeating. Read before every task.

---

<!--
Format:
### [Date] - [Category]: [Brief Title]
**Context:** What happened
**Rule:** ALWAYS/NEVER statement
**Example:** Code example if helpful
-->

<!-- New mistakes will be appended below -->
'''
        ))

        # decisions.md
        self.files.append(GeneratedFile(
            path="docs/memory/decisions.md",
            content='''# Decisions Log

Record of significant decisions. Don't re-debate decided topics.

---

<!--
Format:
### [Date] - [Topic]
**Decision:** What was decided
**Reasoning:** Why this choice
**Alternatives:** What was considered
-->

<!-- New decisions will be appended below -->
'''
        ))

        # discoveries.md
        self.files.append(GeneratedFile(
            path="docs/memory/discoveries.md",
            content='''# Discoveries Log

Insights and patterns discovered during work.

---

<!--
Format:
### [Date] - [Topic]
**Discovery:** What was learned
**Application:** How to use this knowledge
-->

<!-- New discoveries will be appended below -->
'''
        ))

    def _generate_agents(self, answers: dict) -> None:
        """Generate agent definition files."""
        enabled_agents = answers.get("enable_agents", [])

        agent_templates = {
            "Code Reviewer - Quality & security checks": {
                "name": "code-reviewer",
                "description": "Autonomous code quality and security reviewer",
                "tools": "Read, Grep, Glob, Bash(git:*)",
                "content": '''# Code Review Specialist

You are a senior code reviewer focused on quality, security, and maintainability.

## Your Responsibilities
1. Review code for security vulnerabilities
2. Identify performance issues and anti-patterns
3. Check for best practices violations
4. Ensure adequate test coverage

## Output Format
Provide findings categorized by severity:
- **CRITICAL:** Security vulnerabilities, data loss risks
- **HIGH:** Logic errors, missing error handling
- **MEDIUM:** Code quality, performance concerns
- **LOW:** Style, documentation suggestions
'''
            },
            "Architect - Design decisions": {
                "name": "architect",
                "description": "System design and architecture advisor",
                "tools": "Read, Grep, Glob",
                "content": '''# Architecture Advisor

You provide guidance on system design and architecture decisions.

## Your Responsibilities
1. Evaluate architectural trade-offs
2. Suggest design patterns
3. Identify potential scaling issues
4. Recommend separation of concerns

## Output Format
Provide analysis with:
- **Recommendation:** Your suggested approach
- **Trade-offs:** Pros and cons
- **Alternatives:** Other options considered
'''
            },
            "Researcher - Deep investigations": {
                "name": "researcher",
                "description": "Deep research and investigation specialist",
                "tools": "Read, Grep, Glob, Bash(curl:*)",
                "content": '''# Research Specialist

You conduct deep investigations into technical topics.

## Your Responsibilities
1. Research best practices and patterns
2. Investigate library options
3. Analyze existing implementations
4. Synthesize findings into recommendations
'''
            },
            "Debugger - Error analysis": {
                "name": "debugger",
                "description": "Error analysis and debugging specialist",
                "tools": "Read, Grep, Glob, Bash(git:*)",
                "content": '''# Debugging Specialist

You analyze errors and help resolve issues.

## Your Responsibilities
1. Analyze stack traces and error messages
2. Identify root causes
3. Suggest fixes with explanations
4. Verify fixes work correctly
'''
            },
            "Security Auditor - Vulnerability scanning": {
                "name": "security-auditor",
                "description": "Security vulnerability scanner",
                "tools": "Read, Grep, Glob",
                "content": '''# Security Auditor

You scan code for security vulnerabilities.

## Focus Areas
1. Injection vulnerabilities (SQL, command, XSS)
2. Authentication and authorization issues
3. Secrets exposure
4. Insecure dependencies
5. OWASP Top 10 violations
'''
            }
        }

        for agent_label in enabled_agents:
            if agent_label in agent_templates:
                template = agent_templates[agent_label]
                content = f'''---
name: {template["name"]}
description: {template["description"]}
tools: {template["tools"]}
model: claude-sonnet-4-20250514
---

{template["content"]}
'''
                self.files.append(GeneratedFile(
                    path=f".claude/agents/{template['name']}.md",
                    content=content
                ))

    def _generate_commands(self, answers: dict) -> None:
        """Generate command definition files."""
        enabled_commands = answers.get("enable_commands", [])

        command_templates = {
            "/reflect - Learn from mistakes": {
                "name": "reflect",
                "description": "Reflect on a mistake and codify the learning",
                "tools": "Read, Write, Edit",
                "content": '''# Self-Reflection Protocol

You just encountered an issue. Follow this protocol:

## Step 1: Reflect
Analyze what went wrong. Consider:
- What was the root cause?
- What signals did you miss?

## Step 2: Abstract
Extract the general pattern from this specific instance.

## Step 3: Document
Append your learning to `.claude/rules/learned_lessons.md` using this format:

```markdown
### [Date] - [Category]: [Brief Title]
**Context:** [1-2 sentences on what happened]
**Rule:** [ALWAYS/NEVER statement]
```
'''
            },
            "/review - Code review workflow": {
                "name": "review",
                "description": "Run code review on changes",
                "tools": "Read, Grep, Glob, Bash(git:*)",
                "content": '''# Code Review Workflow

Run a comprehensive code review on the specified scope.

## Usage
- `/review staged` - Review staged changes
- `/review branch` - Review current branch vs main
- `/review file path/to/file` - Review specific file

## Process
1. Get the diff for the specified scope
2. Analyze for issues
3. Provide findings by severity
'''
            },
            "/standup - Daily standup summary": {
                "name": "standup",
                "description": "Generate daily standup summary",
                "tools": "Read, Bash(git:*)",
                "content": '''# Daily Standup Summary

Generate a summary for daily standup.

## Output Format
**Yesterday:** What was completed
**Today:** What's planned
**Blockers:** Any issues

## Data Sources
- Git commits from last 24 hours
- Session log entries
- Task status
'''
            },
            "/research - Deep research mode": {
                "name": "research",
                "description": "Deep research on a topic",
                "tools": "Read, Grep, Glob, Bash(curl:*)",
                "content": '''# Deep Research Mode

Conduct thorough research on the specified topic.

## Process
1. Gather information from multiple sources
2. Analyze and synthesize findings
3. Provide recommendations with citations
'''
            },
            "/check - Pre-commit checklist": {
                "name": "check",
                "description": "Pre-commit verification checklist",
                "tools": "Read, Bash(git:*)",
                "content": '''# Pre-Commit Checklist

Verify changes are ready to commit.

## Checks
- [ ] All tests pass
- [ ] Linting passes
- [ ] No secrets in diff
- [ ] Documentation updated
- [ ] Commit message follows conventions
'''
            }
        }

        for cmd_label in enabled_commands:
            if cmd_label in command_templates:
                template = command_templates[cmd_label]
                content = f'''---
allowed-tools: {template["tools"]}
description: {template["description"]}
---

{template["content"]}
'''
                self.files.append(GeneratedFile(
                    path=f".claude/commands/{template['name']}.md",
                    content=content
                ))

    def _generate_models_json(self, answers: dict) -> None:
        """Generate models.json for multi-model support."""
        enabled_models = answers.get("models_to_enable", [])
        enable_optillm = answers.get("enable_optillm", False)
        optillm_technique = answers.get("optillm_technique", "moa - Mixture of Agents")

        models = {}

        if "OpenAI GPT-5.2 Codex" in enabled_models:
            models["openai"] = {
                "enabled": True,
                "model": "gpt-5.2-codex",
                "display_name": "OpenAI GPT-5.2 Codex",
                "api_key_env": "OPENAI_API_KEY",
                "max_tokens": 4096,
                "temperature": 0.1
            }

        if "Google Gemini 3 Pro" in enabled_models:
            models["gemini"] = {
                "enabled": True,
                "model": "gemini-3-pro-preview",
                "display_name": "Google Gemini 3 Pro",
                "api_key_env": "GEMINI_API_KEY",
                "max_tokens": 8192,
                "temperature": 0.1
            }

        if "Anthropic Claude" in enabled_models or any("Claude" in m for m in enabled_models):
            models["claude"] = {
                "enabled": True,
                "model": "claude-sonnet-4-20250514",
                "display_name": "Anthropic Claude Sonnet",
                "api_key_env": "ANTHROPIC_API_KEY",
                "max_tokens": 4096,
                "temperature": 0.1
            }

        # Extract technique ID from label
        technique_id = optillm_technique.split(" - ")[0] if " - " in optillm_technique else "moa"

        config = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "description": "Model configuration for multi-model tasks",
            "models": models,
            "optillm": {
                "enabled": enable_optillm,
                "proxy_url": "http://localhost:8000/v1",
                "technique": technique_id,
                "available_techniques": [
                    {"id": "moa", "name": "Mixture of Agents", "description": "Combines critiques from multiple model instances"},
                    {"id": "cot_reflection", "name": "CoT Reflection", "description": "Chain-of-thought with self-reflection"},
                    {"id": "mcts", "name": "MCTS", "description": "Monte Carlo Tree Search"},
                    {"id": "self_consistency", "name": "Self Consistency", "description": "Multiple samples with majority voting"}
                ]
            },
            "defaults": {
                "code_review": {
                    "models": list(models.keys()),
                    "use_optillm": enable_optillm,
                    "optillm_technique": technique_id
                }
            }
        }

        self.files.append(GeneratedFile(
            path="models.json",
            content=json.dumps(config, indent=2)
        ))

    def _generate_rules(self, answers: dict) -> None:
        """Generate rule files."""
        # learned_lessons.md
        self.files.append(GeneratedFile(
            path=".claude/rules/learned_lessons.md",
            content='''# Learned Lessons

This file contains codified learnings from past mistakes. Read this before starting any task.

---

<!--
Format for new entries:

### [Date] - [Category]: [Brief Title]
**Context:** [1-2 sentences on what happened]
**Rule:** [ALWAYS/NEVER statement]
**Example:** [Optional concrete example]
-->

<!-- New learnings will be appended below this line -->
'''
        ))

        # safety.md
        security_level = answers.get("security_level", "Standard")

        if "Maximum" in security_level or "High" in security_level:
            safety_content = '''# Safety Rules

These rules are NON-NEGOTIABLE. They exist to prevent catastrophic mistakes.

---

## File System Safety

### NEVER modify these files without explicit human approval:
- `.env` or any `.env.*` files
- Lock files (package-lock.json, etc.)
- `.git/` directory contents
- Production configuration files
- Database migration files

### NEVER delete:
- Directories recursively without listing contents first
- Files matching broad glob patterns
- Anything in `/` or `~` directories

---

## Execution Safety

### NEVER run:
- `rm -rf` on directories you didn't create
- Commands with `sudo`
- Scripts downloaded from the internet without review
- Database migrations on production

### ALWAYS:
- Run tests after code changes
- Check git status before committing
- Create backups before bulk operations
- Use `--dry-run` flags when available

---

## Secret Safety

### NEVER:
- Commit secrets to git
- Log sensitive data
- Include real credentials in samples

### ALWAYS:
- Use environment variables for secrets
- Check `.gitignore` includes secret files
'''
        else:
            safety_content = '''# Safety Rules

Basic safety guidelines for this configuration.

---

## Core Rules

- NEVER commit secrets to git
- NEVER run destructive commands without confirmation
- ALWAYS run tests before committing
- ALWAYS check git status before operations
'''

        self.files.append(GeneratedFile(
            path=".claude/rules/safety.md",
            content=safety_content
        ))

    def apply_improvements(self, config: dict, review_results: dict) -> dict:
        """Apply improvements suggested by the reviewer."""
        # This would modify the generated files based on review feedback
        # For now, just return the config as-is
        return config

    def write_config(self, config: dict, output_path: Path) -> None:
        """Write all generated files to the output directory."""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        for file in self.files:
            file_path = output_path / file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file.content)
            print(f"   ✓ Created: {file.path}")
