#!/usr/bin/env python3
"""
API Key Manager - Secure handling of API keys for multi-model features.

Supports multiple storage methods:
- Environment variables
- .env files
- Secure keyring storage
- Interactive input (session-only)
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Try to import keyring for secure storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


@dataclass
class APIKeyConfig:
    """Configuration for an API key."""
    name: str
    env_var: str
    display_name: str
    required_for: list[str]
    validation_url: str = ""
    help_url: str = ""


class APIKeyManager:
    """Manages API keys for the config pipeline."""

    SUPPORTED_KEYS = [
        APIKeyConfig(
            name="openai",
            env_var="OPENAI_API_KEY",
            display_name="OpenAI API Key",
            required_for=["multi-model review", "GPT-5.2 code review"],
            help_url="https://platform.openai.com/api-keys"
        ),
        APIKeyConfig(
            name="gemini",
            env_var="GEMINI_API_KEY",
            display_name="Google Gemini API Key",
            required_for=["multi-model review", "Gemini 3 code review"],
            help_url="https://aistudio.google.com/app/apikey"
        ),
        APIKeyConfig(
            name="anthropic",
            env_var="ANTHROPIC_API_KEY",
            display_name="Anthropic API Key",
            required_for=["Claude model in multi-model review"],
            help_url="https://console.anthropic.com/settings/keys"
        ),
    ]

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".config" / "config-setup-pipeline"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.env_file = self.config_dir / ".env"

    def get_key(self, key_name: str) -> Optional[str]:
        """Get an API key from any available source."""
        key_config = self._get_key_config(key_name)
        if not key_config:
            return None

        # Priority: env var > .env file > keyring
        # 1. Check environment variable
        value = os.environ.get(key_config.env_var)
        if value:
            return value

        # 2. Check .env file
        value = self._load_from_env_file(key_config.env_var)
        if value:
            return value

        # 3. Check keyring
        if KEYRING_AVAILABLE:
            value = self._load_from_keyring(key_config.env_var)
            if value:
                return value

        return None

    def set_key(self, key_name: str, value: str, storage: str = "env_file") -> bool:
        """Store an API key."""
        key_config = self._get_key_config(key_name)
        if not key_config:
            return False

        if storage == "env_file":
            return self._save_to_env_file(key_config.env_var, value)
        elif storage == "keyring" and KEYRING_AVAILABLE:
            return self._save_to_keyring(key_config.env_var, value)
        elif storage == "session":
            os.environ[key_config.env_var] = value
            return True

        return False

    def validate_key(self, key_name: str, key_value: str) -> tuple[bool, str]:
        """Validate an API key by making a test request."""
        key_config = self._get_key_config(key_name)
        if not key_config:
            return False, "Unknown key type"

        if key_name == "openai":
            return self._validate_openai(key_value)
        elif key_name == "gemini":
            return self._validate_gemini(key_value)
        elif key_name == "anthropic":
            return self._validate_anthropic(key_value)

        return True, "Validation not implemented for this key type"

    def get_status(self) -> dict:
        """Get status of all API keys."""
        status = {}
        for key_config in self.SUPPORTED_KEYS:
            value = self.get_key(key_config.name)
            status[key_config.name] = {
                "display_name": key_config.display_name,
                "env_var": key_config.env_var,
                "configured": bool(value),
                "masked_value": self._mask_key(value) if value else None,
                "required_for": key_config.required_for,
                "help_url": key_config.help_url
            }
        return status

    def interactive_setup(self) -> dict:
        """Run interactive setup for API keys."""
        print("\n" + "=" * 60)
        print("🔑 API KEY SETUP")
        print("=" * 60)
        print("\nAPI keys enable powerful features like multi-model code review.")
        print("Keys are stored securely and never shared.\n")

        configured = {}

        for key_config in self.SUPPORTED_KEYS:
            existing = self.get_key(key_config.name)

            print(f"\n{key_config.display_name}")
            print(f"   Used for: {', '.join(key_config.required_for)}")
            print(f"   Get key at: {key_config.help_url}")

            if existing:
                print(f"   Current: {self._mask_key(existing)}")
                update = input("   Update this key? [y/N]: ").strip().lower()
                if update != 'y':
                    configured[key_config.name] = True
                    continue

            key_value = input(f"   Enter {key_config.display_name} (or press Enter to skip): ").strip()

            if not key_value:
                print("   ⏭ Skipped")
                continue

            # Validate
            print("   Validating...")
            valid, message = self.validate_key(key_config.name, key_value)

            if valid:
                print(f"   ✓ Valid: {message}")

                # Ask where to store
                print("\n   Storage options:")
                print("   1. Local .env file (recommended)")
                if KEYRING_AVAILABLE:
                    print("   2. System keyring (most secure)")
                print("   3. Session only (temporary)")

                choice = input("   Choose storage [1]: ").strip() or "1"

                storage_map = {"1": "env_file", "2": "keyring", "3": "session"}
                storage = storage_map.get(choice, "env_file")

                if self.set_key(key_config.name, key_value, storage):
                    print(f"   ✓ Saved to {storage}")
                    configured[key_config.name] = True
                else:
                    print("   ✗ Failed to save")
            else:
                print(f"   ✗ Invalid: {message}")
                retry = input("   Try again? [Y/n]: ").strip().lower()
                if retry != 'n':
                    # Recursive retry (simplified)
                    pass

        return configured

    def _get_key_config(self, key_name: str) -> Optional[APIKeyConfig]:
        """Get config for a key by name."""
        for config in self.SUPPORTED_KEYS:
            if config.name == key_name:
                return config
        return None

    def _mask_key(self, key: str) -> str:
        """Mask a key for display."""
        if len(key) <= 8:
            return "*" * len(key)
        return key[:4] + "*" * (len(key) - 8) + key[-4:]

    def _load_from_env_file(self, var_name: str) -> Optional[str]:
        """Load a value from the .env file."""
        if not self.env_file.exists():
            return None

        try:
            content = self.env_file.read_text()
            for line in content.split("\n"):
                if line.startswith(f"{var_name}="):
                    value = line[len(var_name) + 1:].strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    return value
        except Exception:
            pass
        return None

    def _save_to_env_file(self, var_name: str, value: str) -> bool:
        """Save a value to the .env file."""
        try:
            lines = []
            found = False

            if self.env_file.exists():
                content = self.env_file.read_text()
                for line in content.split("\n"):
                    if line.startswith(f"{var_name}="):
                        lines.append(f'{var_name}="{value}"')
                        found = True
                    elif line.strip():
                        lines.append(line)

            if not found:
                lines.append(f'{var_name}="{value}"')

            self.env_file.write_text("\n".join(lines) + "\n")

            # Set file permissions to owner-only
            os.chmod(self.env_file, 0o600)

            # Also set in current environment
            os.environ[var_name] = value

            return True
        except Exception as e:
            print(f"   Error saving to .env: {e}")
            return False

    def _load_from_keyring(self, var_name: str) -> Optional[str]:
        """Load a value from the system keyring."""
        if not KEYRING_AVAILABLE:
            return None
        try:
            return keyring.get_password("config-setup-pipeline", var_name)
        except Exception:
            return None

    def _save_to_keyring(self, var_name: str, value: str) -> bool:
        """Save a value to the system keyring."""
        if not KEYRING_AVAILABLE:
            return False
        try:
            keyring.set_password("config-setup-pipeline", var_name, value)
            os.environ[var_name] = value
            return True
        except Exception:
            return False

    def _validate_openai(self, key: str) -> tuple[bool, str]:
        """Validate OpenAI API key."""
        try:
            import openai
            client = openai.OpenAI(api_key=key)
            # Make a minimal request
            models = client.models.list()
            return True, f"Connected (found {len(list(models))} models)"
        except Exception as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg.lower():
                return False, "Invalid API key"
            elif "rate_limit" in error_msg.lower():
                return True, "Valid (rate limited but working)"
            return False, f"Error: {error_msg[:50]}"

    def _validate_gemini(self, key: str) -> tuple[bool, str]:
        """Validate Gemini API key."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            models = list(genai.list_models())
            return True, f"Connected (found {len(models)} models)"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"

    def _validate_anthropic(self, key: str) -> tuple[bool, str]:
        """Validate Anthropic API key."""
        try:
            # Simple validation - check key format
            if key.startswith("sk-ant-"):
                return True, "Key format valid"
            return False, "Invalid key format (should start with sk-ant-)"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"

    def load_env_file(self) -> None:
        """Load all keys from .env file into environment."""
        if not self.env_file.exists():
            return

        try:
            content = self.env_file.read_text()
            for line in content.split("\n"):
                if "=" in line and not line.startswith("#"):
                    var, _, value = line.partition("=")
                    var = var.strip()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    if var and value:
                        os.environ[var] = value
        except Exception:
            pass
