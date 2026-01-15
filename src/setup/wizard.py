#!/usr/bin/env python3
"""
Setup Wizard - First-time setup and configuration discovery.

Handles:
- API key configuration
- Existing config discovery
- User preferences
- Feature selection
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .api_keys import APIKeyManager


@dataclass
class UserProfile:
    """User profile with preferences and discovered configs."""
    name: str
    configs_path: Optional[Path]
    discovered_configs: list[str]
    api_keys_configured: list[str]
    preferences: dict


class SetupWizard:
    """First-time setup wizard."""

    CONFIG_FILE = "user_profile.json"

    # Common locations to search for existing Claude configs
    SEARCH_PATHS = [
        Path.home() / "claude-configs",
        Path.home() / ".claude",
        Path.home() / ".config" / "claude",
        Path.home() / "Documents" / "claude-configs",
        Path.home() / "Projects",
        Path.home() / "code",
        Path.home() / "dev",
    ]

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".config" / "config-setup-pipeline"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.config_dir / self.CONFIG_FILE
        self.api_key_manager = APIKeyManager(self.config_dir)

    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        return not self.profile_path.exists()

    def load_profile(self) -> Optional[UserProfile]:
        """Load existing user profile."""
        if not self.profile_path.exists():
            return None

        try:
            data = json.loads(self.profile_path.read_text())
            return UserProfile(
                name=data.get("name", "User"),
                configs_path=Path(data["configs_path"]) if data.get("configs_path") else None,
                discovered_configs=data.get("discovered_configs", []),
                api_keys_configured=data.get("api_keys_configured", []),
                preferences=data.get("preferences", {})
            )
        except Exception:
            return None

    def save_profile(self, profile: UserProfile) -> None:
        """Save user profile."""
        data = {
            "name": profile.name,
            "configs_path": str(profile.configs_path) if profile.configs_path else None,
            "discovered_configs": profile.discovered_configs,
            "api_keys_configured": profile.api_keys_configured,
            "preferences": profile.preferences
        }
        self.profile_path.write_text(json.dumps(data, indent=2))

    def run_setup(self) -> UserProfile:
        """Run the complete setup wizard."""
        print("\n" + "=" * 60)
        print("🚀 WELCOME TO CONFIG SETUP PIPELINE")
        print("=" * 60)
        print("\nThis wizard will help you set up the config generator.")
        print("You only need to do this once.\n")

        # Step 1: Get user name
        name = input("What should I call you? [Boss]: ").strip() or "Boss"
        print(f"\nNice to meet you, {name}! 👋\n")

        # Step 2: Discover existing configs
        print("=" * 60)
        print("📂 DISCOVERING EXISTING CONFIGURATIONS")
        print("=" * 60)

        discovered_configs = self._discover_configs()

        if discovered_configs:
            print(f"\n✓ Found {len(discovered_configs)} existing configuration(s):")
            for config in discovered_configs[:5]:
                print(f"   • {config}")
            if len(discovered_configs) > 5:
                print(f"   ... and {len(discovered_configs) - 5} more")

            use_discovered = input("\nUse these for learning patterns? [Y/n]: ").strip().lower()
            if use_discovered == 'n':
                discovered_configs = []
        else:
            print("\nNo existing configurations found.")
            print("No worries! We'll create a fresh configuration.\n")

        # Ask for custom path
        custom_path = input("\nPath to your configs directory (or Enter to skip): ").strip()
        configs_path = Path(custom_path).expanduser() if custom_path else None

        if configs_path and configs_path.exists():
            extra_configs = self._scan_directory(configs_path)
            discovered_configs.extend(extra_configs)
            print(f"   ✓ Found {len(extra_configs)} additional configs")

        # Step 3: API Keys
        print("\n")
        api_keys_configured = []

        setup_keys = input("Set up API keys for multi-model features? [Y/n]: ").strip().lower()
        if setup_keys != 'n':
            configured = self.api_key_manager.interactive_setup()
            api_keys_configured = [k for k, v in configured.items() if v]
        else:
            print("\n⏭ Skipping API key setup.")
            print("   You can set up keys later with: config-setup --setup-keys")

        # Step 4: Preferences
        print("\n" + "=" * 60)
        print("⚙️ PREFERENCES")
        print("=" * 60)

        preferences = self._collect_preferences()

        # Create and save profile
        profile = UserProfile(
            name=name,
            configs_path=configs_path,
            discovered_configs=list(set(discovered_configs)),
            api_keys_configured=api_keys_configured,
            preferences=preferences
        )

        self.save_profile(profile)

        # Summary
        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETE")
        print("=" * 60)
        print(f"\nProfile saved to: {self.profile_path}")
        print(f"Discovered configs: {len(profile.discovered_configs)}")
        print(f"API keys configured: {len(profile.api_keys_configured)}")

        print("\nYou're ready to create configurations!")
        print("Run: config-setup")
        print("Or:  python -m src.main")

        return profile

    def _discover_configs(self) -> list[str]:
        """Discover existing Claude configurations."""
        discovered = []

        print("\nSearching common locations...")
        for search_path in self.SEARCH_PATHS:
            if search_path.exists():
                configs = self._scan_directory(search_path)
                discovered.extend(configs)

        return list(set(discovered))

    def _scan_directory(self, directory: Path, depth: int = 3) -> list[str]:
        """Scan a directory for Claude configurations."""
        configs = []

        try:
            # Look for CLAUDE.md files
            for claude_md in directory.rglob("CLAUDE.md"):
                # Limit depth
                relative = claude_md.relative_to(directory)
                if len(relative.parts) <= depth:
                    configs.append(str(claude_md.parent))

            # Look for .claude directories
            for claude_dir in directory.rglob(".claude"):
                if claude_dir.is_dir():
                    relative = claude_dir.relative_to(directory)
                    if len(relative.parts) <= depth:
                        parent = str(claude_dir.parent)
                        if parent not in configs:
                            configs.append(parent)

        except PermissionError:
            pass

        return configs

    def _collect_preferences(self) -> dict:
        """Collect user preferences."""
        preferences = {}

        print("\nA few quick preferences (press Enter for defaults):\n")

        # Default autonomy level
        print("Default autonomy level for generated configs:")
        print("   1. Co-founder (highly autonomous)")
        print("   2. Senior dev (autonomous with check-ins)")
        print("   3. Assistant (asks questions)")
        autonomy = input("Choose [1]: ").strip() or "1"
        preferences["default_autonomy"] = {"1": "cofounder", "2": "senior", "3": "assistant"}.get(autonomy, "cofounder")

        # Default security level
        print("\nDefault security level:")
        print("   1. Relaxed (personal projects)")
        print("   2. Standard (general development)")
        print("   3. High (production systems)")
        security = input("Choose [2]: ").strip() or "2"
        preferences["default_security"] = {"1": "relaxed", "2": "standard", "3": "high"}.get(security, "standard")

        # Multi-model by default
        multi = input("\nEnable multi-model review by default? [Y/n]: ").strip().lower()
        preferences["multi_model_default"] = multi != 'n'

        # Research by default
        research = input("Run best practices research by default? [Y/n]: ").strip().lower()
        preferences["research_default"] = research != 'n'

        # Verbose output
        verbose = input("Show detailed output during generation? [y/N]: ").strip().lower()
        preferences["verbose"] = verbose == 'y'

        return preferences

    def ensure_setup(self) -> UserProfile:
        """Ensure setup is complete, running wizard if needed."""
        # Load .env file first
        self.api_key_manager.load_env_file()

        if self.is_first_run():
            return self.run_setup()

        profile = self.load_profile()
        if profile:
            # Reload API keys
            self.api_key_manager.load_env_file()
            return profile

        return self.run_setup()

    def quick_setup(self) -> UserProfile:
        """Quick setup with sensible defaults."""
        # Load existing .env if present
        self.api_key_manager.load_env_file()

        # Check for API keys in environment
        api_keys = []
        for key_config in self.api_key_manager.SUPPORTED_KEYS:
            if os.environ.get(key_config.env_var):
                api_keys.append(key_config.name)

        # Quick config discovery
        discovered = self._discover_configs()

        profile = UserProfile(
            name="User",
            configs_path=None,
            discovered_configs=discovered[:10],  # Limit for speed
            api_keys_configured=api_keys,
            preferences={
                "default_autonomy": "cofounder",
                "default_security": "standard",
                "multi_model_default": len(api_keys) > 0,
                "research_default": True,
                "verbose": False
            }
        )

        self.save_profile(profile)
        return profile
