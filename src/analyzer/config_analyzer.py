#!/usr/bin/env python3
"""
Config Analyzer - Learns from existing Claude Code configurations.

Extracts patterns from:
- CLAUDE.md files
- settings.json configurations
- Agent definitions
- Command definitions
- Hook patterns
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ConfigPattern:
    """A pattern extracted from a configuration."""
    type: str  # claude_md, settings, agent, command, hook
    name: str
    source: str
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class ExtractedAgent:
    """An agent definition extracted from configs."""
    name: str
    description: str
    tools: list[str]
    model: str
    instructions: str


@dataclass
class ExtractedCommand:
    """A command definition extracted from configs."""
    name: str
    description: str
    allowed_tools: list[str]
    instructions: str


@dataclass
class ExtractedHook:
    """A hook pattern extracted from configs."""
    event: str  # PostToolUse, PreToolUse, Stop, etc.
    matcher: str
    command: str
    purpose: str = ""


class ConfigAnalyzer:
    """Analyzes existing configurations to extract patterns."""

    def __init__(self, configs_path: str):
        self.configs_path = Path(configs_path)
        self.patterns: list[ConfigPattern] = []
        self.agents: list[ExtractedAgent] = []
        self.commands: list[ExtractedCommand] = []
        self.hooks: list[ExtractedHook] = []
        self.settings_patterns: list[dict] = []

    def analyze(self) -> dict:
        """Analyze all configurations and extract patterns."""
        if not self.configs_path.exists():
            return {}

        # Find all config directories
        config_dirs = self._find_config_dirs()

        for config_dir in config_dirs:
            self._analyze_config_dir(config_dir)

        return {
            "configs": [p.name for p in config_dirs],
            "patterns": [
                {"type": p.type, "name": p.name, "source": p.source}
                for p in self.patterns
            ],
            "agents": [
                {"name": a.name, "description": a.description, "tools": a.tools}
                for a in self.agents
            ],
            "commands": [
                {"name": c.name, "description": c.description}
                for c in self.commands
            ],
            "hooks": [
                {"event": h.event, "matcher": h.matcher, "purpose": h.purpose}
                for h in self.hooks
            ],
            "settings_patterns": self.settings_patterns,
        }

    def _find_config_dirs(self) -> list[Path]:
        """Find directories containing Claude configurations."""
        config_dirs = []

        # Look for CLAUDE.md files
        for claude_md in self.configs_path.rglob("CLAUDE.md"):
            config_dirs.append(claude_md.parent)

        # Look for .claude directories
        for claude_dir in self.configs_path.rglob(".claude"):
            if claude_dir.is_dir():
                parent = claude_dir.parent
                if parent not in config_dirs:
                    config_dirs.append(parent)

        return list(set(config_dirs))

    def _analyze_config_dir(self, config_dir: Path) -> None:
        """Analyze a single configuration directory."""
        # Analyze CLAUDE.md
        claude_md = config_dir / "CLAUDE.md"
        if claude_md.exists():
            self._analyze_claude_md(claude_md)

        # Analyze settings.json
        settings_file = config_dir / ".claude" / "settings.json"
        if settings_file.exists():
            self._analyze_settings(settings_file)

        # Analyze agents
        agents_dir = config_dir / ".claude" / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                self._analyze_agent(agent_file)

        # Analyze commands
        commands_dir = config_dir / ".claude" / "commands"
        if commands_dir.exists():
            for cmd_file in commands_dir.glob("*.md"):
                self._analyze_command(cmd_file)

    def _analyze_claude_md(self, path: Path) -> None:
        """Extract patterns from a CLAUDE.md file."""
        content = path.read_text()

        # Extract identity pattern
        identity_match = re.search(r'[Aa]ddress me as ["\']?(\w+)["\']?', content)
        if identity_match:
            self.patterns.append(ConfigPattern(
                type="identity",
                name=identity_match.group(1),
                source=str(path),
                content=identity_match.group(0)
            ))

        # Extract tech stack
        tech_match = re.search(r'## Tech Stack\s*\n([\s\S]*?)(?=\n##|\Z)', content)
        if tech_match:
            self.patterns.append(ConfigPattern(
                type="tech_stack",
                name="tech_stack",
                source=str(path),
                content=tech_match.group(1).strip()
            ))

        # Extract commands section
        commands_match = re.search(r'## Commands\s*\n([\s\S]*?)(?=\n##|\Z)', content)
        if commands_match:
            self.patterns.append(ConfigPattern(
                type="commands",
                name="build_commands",
                source=str(path),
                content=commands_match.group(1).strip()
            ))

        # Extract before/after task patterns
        before_match = re.search(r'## Before Any Task\s*\n([\s\S]*?)(?=\n##|\Z)', content)
        if before_match:
            self.patterns.append(ConfigPattern(
                type="checklist",
                name="before_task",
                source=str(path),
                content=before_match.group(1).strip()
            ))

        after_match = re.search(r'## After Any Task\s*\n([\s\S]*?)(?=\n##|\Z)', content)
        if after_match:
            self.patterns.append(ConfigPattern(
                type="checklist",
                name="after_task",
                source=str(path),
                content=after_match.group(1).strip()
            ))

    def _analyze_settings(self, path: Path) -> None:
        """Extract patterns from settings.json."""
        try:
            settings = json.loads(path.read_text())

            # Extract permissions pattern
            permissions = settings.get("permissions", {})
            allow = permissions.get("allow", [])
            deny = permissions.get("deny", [])

            self.settings_patterns.append({
                "source": str(path),
                "allow_count": len(allow),
                "deny_count": len(deny),
                "allow_sample": allow[:5],
                "deny_sample": deny[:5]
            })

            # Extract hook patterns
            hooks = settings.get("hooks", {})
            for event, hook_list in hooks.items():
                for hook_config in hook_list:
                    matcher = hook_config.get("matcher", "*")
                    for hook in hook_config.get("hooks", []):
                        self.hooks.append(ExtractedHook(
                            event=event,
                            matcher=matcher,
                            command=hook.get("command", ""),
                            purpose=self._infer_hook_purpose(hook.get("command", ""))
                        ))

        except (json.JSONDecodeError, Exception) as e:
            pass

    def _analyze_agent(self, path: Path) -> None:
        """Extract patterns from an agent definition."""
        content = path.read_text()

        # Parse YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)

            name = re.search(r'name:\s*(.+)', frontmatter)
            description = re.search(r'description:\s*(.+)', frontmatter)
            tools = re.search(r'tools:\s*(.+)', frontmatter)
            model = re.search(r'model:\s*(.+)', frontmatter)

            self.agents.append(ExtractedAgent(
                name=name.group(1).strip() if name else path.stem,
                description=description.group(1).strip() if description else "",
                tools=tools.group(1).strip().split(", ") if tools else [],
                model=model.group(1).strip() if model else "default",
                instructions=content[frontmatter_match.end():].strip()
            ))

    def _analyze_command(self, path: Path) -> None:
        """Extract patterns from a command definition."""
        content = path.read_text()

        # Parse YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)

            description = re.search(r'description:\s*(.+)', frontmatter)
            allowed_tools = re.search(r'allowed-tools:\s*(.+)', frontmatter)

            self.commands.append(ExtractedCommand(
                name=path.stem,
                description=description.group(1).strip() if description else "",
                allowed_tools=allowed_tools.group(1).strip().split(", ") if allowed_tools else [],
                instructions=content[frontmatter_match.end():].strip()
            ))

    def _infer_hook_purpose(self, command: str) -> str:
        """Infer the purpose of a hook from its command."""
        command_lower = command.lower()

        if "safety" in command_lower:
            return "Safety check"
        elif "metric" in command_lower:
            return "Metrics collection"
        elif "track" in command_lower:
            return "File tracking"
        elif "lint" in command_lower:
            return "Linting"
        elif "notify" in command_lower:
            return "Notification"
        elif "summary" in command_lower:
            return "Session summary"
        elif "reflex" in command_lower or "reflect" in command_lower:
            return "Self-reflection"
        else:
            return "Custom"

    def print_summary(self, patterns: dict) -> None:
        """Print a human-readable summary of extracted patterns."""
        print("\n" + "=" * 60)
        print("📊 CONFIG ANALYSIS SUMMARY")
        print("=" * 60)

        print(f"\nConfigurations found: {len(patterns.get('configs', []))}")
        for config in patterns.get("configs", []):
            print(f"   • {config}")

        print(f"\nAgents extracted: {len(patterns.get('agents', []))}")
        for agent in patterns.get("agents", []):
            print(f"   • {agent['name']}: {agent['description'][:50]}...")

        print(f"\nCommands extracted: {len(patterns.get('commands', []))}")
        for cmd in patterns.get("commands", []):
            print(f"   • /{cmd['name']}: {cmd['description'][:50]}...")

        print(f"\nHooks patterns: {len(patterns.get('hooks', []))}")
        hook_events = {}
        for hook in patterns.get("hooks", []):
            event = hook["event"]
            hook_events[event] = hook_events.get(event, 0) + 1

        for event, count in hook_events.items():
            print(f"   • {event}: {count} hooks")

        print("\n" + "=" * 60)
