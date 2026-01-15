#!/usr/bin/env python3
"""
Config Reviewer - Multi-model review of generated configurations.

Uses GPT-5.2 and Gemini 3 to review configurations for:
- Security issues
- Best practice violations
- Missing components
- Improvement opportunities
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Check for required packages
try:
    import openai
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "openai"])
    import openai

try:
    import google.generativeai as genai
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "google-generativeai"])
    import google.generativeai as genai


@dataclass
class ReviewIssue:
    """A single issue found during review."""
    severity: str  # critical, high, medium, low
    category: str  # security, best_practice, missing, improvement
    message: str
    suggestion: str
    source: str  # which model found it
    file: str = ""
    confidence: int = 80


REVIEW_PROMPT = """You are an expert Claude Code configuration reviewer.

Review the following configuration for:
1. **Security issues** - Permissions too broad, missing denials, exposed secrets
2. **Best practice violations** - Missing patterns, anti-patterns
3. **Missing components** - Essential elements not present
4. **Improvement opportunities** - Ways to enhance effectiveness

Respond with ONLY valid JSON (no markdown code blocks):
{{"issues": [{{"severity": "critical|high|medium|low", "category": "security|best_practice|missing|improvement", "message": "description under 100 chars", "suggestion": "fix under 100 chars", "file": "filename if applicable", "confidence": 85}}]}}

Only include findings with confidence >= 80.

CONFIGURATION TO REVIEW:
{config}
"""


class ConfigReviewer:
    """Multi-model configuration reviewer."""

    def __init__(self):
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.issues: list[ReviewIssue] = []

    def review(self, config: dict) -> dict:
        """Review a generated configuration."""
        # Build config summary for review
        config_text = self._build_config_text(config)

        # Run parallel reviews
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}

            if self.openai_key:
                futures[executor.submit(self._review_with_openai, config_text)] = "OpenAI"

            if self.gemini_key:
                futures[executor.submit(self._review_with_gemini, config_text)] = "Gemini"

            for future in as_completed(futures):
                model = futures[future]
                try:
                    issues = future.result()
                    print(f"   [{model}] Found {len(issues)} issues")
                    self.issues.extend(issues)
                except Exception as e:
                    print(f"   [{model}] Error: {e}")

        # Deduplicate issues
        unique_issues = self._deduplicate_issues()

        return {
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "suggestion": i.suggestion,
                    "source": i.source,
                    "file": i.file,
                    "confidence": i.confidence
                }
                for i in unique_issues
            ],
            "summary": {
                "total": len(unique_issues),
                "critical": len([i for i in unique_issues if i.severity == "critical"]),
                "high": len([i for i in unique_issues if i.severity == "high"]),
                "medium": len([i for i in unique_issues if i.severity == "medium"]),
                "low": len([i for i in unique_issues if i.severity == "low"])
            }
        }

    def review_path(self, config_path: Path) -> dict:
        """Review a configuration from a file path."""
        config_text = self._read_config_files(config_path)

        # Store as pseudo-config for review
        pseudo_config = {"_raw_content": config_text}
        return self.review(pseudo_config)

    def _build_config_text(self, config: dict) -> str:
        """Build a text representation of the config for review."""
        if "_raw_content" in config:
            return config["_raw_content"]

        files = config.get("files", [])
        answers = config.get("answers", {})

        text = f"Configuration: {config.get('config_name', 'unnamed')}\n"
        text += f"Files generated: {len(files)}\n\n"

        text += "Key settings:\n"
        for key in ["security_level", "autonomy_level", "enable_multi_model", "enable_memory"]:
            if key in answers:
                text += f"  - {key}: {answers[key]}\n"

        text += f"\nFiles: {', '.join(f['path'] for f in files)}\n"

        return text

    def _read_config_files(self, config_path: Path) -> str:
        """Read all config files from a path."""
        text = f"Configuration at: {config_path}\n\n"

        # Read CLAUDE.md
        claude_md = config_path / "CLAUDE.md"
        if claude_md.exists():
            text += f"=== CLAUDE.md ===\n{claude_md.read_text()[:2000]}\n\n"

        # Read settings.json
        settings = config_path / ".claude" / "settings.json"
        if settings.exists():
            text += f"=== settings.json ===\n{settings.read_text()}\n\n"

        # Read models.json
        models = config_path / "models.json"
        if models.exists():
            text += f"=== models.json ===\n{models.read_text()}\n\n"

        return text

    def _review_with_openai(self, config_text: str) -> list[ReviewIssue]:
        """Review using OpenAI GPT-5.2."""
        try:
            client = openai.OpenAI(api_key=self.openai_key)

            response = client.chat.completions.create(
                model="gpt-5.2-codex",
                messages=[
                    {"role": "system", "content": "You are an expert config reviewer. Respond only with valid JSON."},
                    {"role": "user", "content": REVIEW_PROMPT.format(config=config_text[:10000])}
                ],
                max_tokens=2048,
                temperature=0.1
            )

            content = response.choices[0].message.content
            if not content:
                return []

            data = self._extract_json(content)
            return self._parse_issues(data, "OpenAI GPT-5.2")

        except Exception as e:
            print(f"   [OpenAI] Error: {e}")
            return []

    def _review_with_gemini(self, config_text: str) -> list[ReviewIssue]:
        """Review using Google Gemini 3."""
        try:
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel("gemini-3-pro-preview")

            response = model.generate_content(
                REVIEW_PROMPT.format(config=config_text[:10000]),
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=2048
                )
            )

            if not response.candidates or not response.candidates[0].content.parts:
                return []

            content = response.text
            data = self._extract_json(content)
            return self._parse_issues(data, "Google Gemini 3")

        except Exception as e:
            print(f"   [Gemini] Error: {e}")
            return []

    def _extract_json(self, content: str) -> dict:
        """Extract JSON from response."""
        try:
            content = content.strip()

            if content.startswith("{"):
                return json.loads(content)

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]

            content = content.strip()
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                content = content[start:end]

            return json.loads(content)

        except json.JSONDecodeError:
            return {"issues": []}

    def _parse_issues(self, data: dict, source: str) -> list[ReviewIssue]:
        """Parse issues from JSON response."""
        issues = []
        for item in data.get("issues", []):
            if item.get("confidence", 0) >= 80:
                issues.append(ReviewIssue(
                    severity=item.get("severity", "medium"),
                    category=item.get("category", "improvement"),
                    message=item.get("message", ""),
                    suggestion=item.get("suggestion", ""),
                    source=source,
                    file=item.get("file", ""),
                    confidence=item.get("confidence", 80)
                ))
        return issues

    def _deduplicate_issues(self) -> list[ReviewIssue]:
        """Remove duplicate issues across models."""
        seen = set()
        unique = []

        for issue in self.issues:
            key = (issue.category, issue.message[:50].lower())
            if key not in seen:
                seen.add(key)
                unique.append(issue)

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unique.sort(key=lambda i: (severity_order.get(i.severity, 4), -i.confidence))

        return unique

    def print_results(self, results: dict) -> None:
        """Print review results."""
        print("\n" + "=" * 60)
        print("🔬 CONFIGURATION REVIEW RESULTS")
        print("=" * 60)

        summary = results.get("summary", {})
        print(f"\nTotal issues: {summary.get('total', 0)}")
        print(f"  Critical: {summary.get('critical', 0)}")
        print(f"  High: {summary.get('high', 0)}")
        print(f"  Medium: {summary.get('medium', 0)}")
        print(f"  Low: {summary.get('low', 0)}")

        current_severity = None
        for issue in results.get("issues", []):
            if issue["severity"] != current_severity:
                current_severity = issue["severity"]
                print(f"\n--- {current_severity.upper()} ---")

            print(f"\n[{issue['source']}] {issue['message']}")
            print(f"   → {issue['suggestion']}")

        print("\n" + "=" * 60)
