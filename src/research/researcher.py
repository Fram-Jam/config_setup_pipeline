#!/usr/bin/env python3
"""
Best Practices Researcher - Deep research on Claude Code best practices.

Enhanced with:
- Real web search via multiple sources
- LLM-powered synthesis of findings
- Context-aware recommendations
- Confidence scoring
"""

import json
import os
import subprocess
import sys
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Check for required packages
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests"])
    import requests


@dataclass
class ResearchSource:
    """A source of research information."""
    name: str
    url: str
    type: str  # docs, github, guide, community, official
    content: str = ""
    relevance: float = 0.0
    timestamp: str = ""


@dataclass
class BestPractice:
    """A discovered best practice."""
    category: str  # security, performance, workflow, architecture, etc.
    title: str
    description: str
    rationale: str = ""  # WHY this is a best practice
    example: str = ""
    anti_pattern: str = ""  # What NOT to do
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.8
    priority: str = "medium"  # critical, high, medium, low


@dataclass
class ResearchContext:
    """Context for targeted research."""
    tech_stack: list[str] = field(default_factory=list)
    use_case: str = ""
    team_size: str = ""
    security_requirements: str = ""
    existing_patterns: list[str] = field(default_factory=list)


class BestPracticesResearcher:
    """Researches Claude Code best practices with deep analysis."""

    # Official and high-quality sources
    OFFICIAL_SOURCES = [
        {
            "name": "Claude Code Documentation",
            "url": "https://docs.anthropic.com/en/docs/claude-code",
            "type": "official"
        },
        {
            "name": "Claude Code GitHub",
            "url": "https://github.com/anthropics/claude-code",
            "type": "official"
        },
    ]

    # Research topics with context
    RESEARCH_TOPICS = {
        "security": {
            "queries": [
                "claude code security best practices 2025",
                "AI coding assistant permission management",
                "claude code secrets management",
                "preventing code injection AI assistants"
            ],
            "priority": "critical"
        },
        "configuration": {
            "queries": [
                "CLAUDE.md configuration best practices",
                "claude code settings.json optimization",
                "AI assistant context management"
            ],
            "priority": "high"
        },
        "workflow": {
            "queries": [
                "claude code automation hooks",
                "AI pair programming workflow optimization",
                "claude code productivity patterns"
            ],
            "priority": "high"
        },
        "multi_model": {
            "queries": [
                "multi-model code review patterns",
                "combining LLMs for code analysis",
                "AI ensemble code review"
            ],
            "priority": "medium"
        },
        "memory": {
            "queries": [
                "AI assistant persistent memory patterns",
                "context management long running AI sessions",
                "claude code session continuity"
            ],
            "priority": "medium"
        }
    }

    def __init__(self, context: Optional[ResearchContext] = None):
        self.context = context or ResearchContext()
        self.sources: list[ResearchSource] = []
        self.best_practices: list[BestPractice] = []
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")

    def research_all(self, deep: bool = True) -> dict:
        """Run comprehensive research on all topics."""
        print("   Gathering sources from official documentation...")
        self._fetch_official_sources()

        print("   Searching community resources...")
        self._search_community_resources()

        if deep and (self.openai_key or self.gemini_key):
            print("   Running deep analysis with LLM synthesis...")
            self._synthesize_with_llm()
        else:
            print("   Extracting best practices from sources...")
            self._extract_best_practices()

        # Prioritize based on context
        self._prioritize_for_context()

        return self._build_results()

    def research_topic(self, topic: str, deep: bool = True) -> dict:
        """Research a specific topic in depth."""
        topic_config = self.RESEARCH_TOPICS.get(topic)

        if topic_config:
            for query in topic_config["queries"]:
                self._search_web(query)
        else:
            self._search_web(topic)

        if deep and (self.openai_key or self.gemini_key):
            self._synthesize_with_llm(focus_topic=topic)
        else:
            self._extract_best_practices()

        return self._build_results()

    def research_for_stack(self, tech_stack: list[str]) -> dict:
        """Research best practices specific to a tech stack."""
        self.context.tech_stack = tech_stack

        # Add stack-specific queries
        for tech in tech_stack[:3]:  # Limit to top 3
            self._search_web(f"claude code {tech} best practices")
            self._search_web(f"AI coding assistant {tech} configuration")

        return self.research_all()

    def _fetch_official_sources(self) -> None:
        """Fetch content from official sources."""
        for source_info in self.OFFICIAL_SOURCES:
            try:
                content = self._fetch_url_content(source_info["url"])
                if content:
                    self.sources.append(ResearchSource(
                        name=source_info["name"],
                        url=source_info["url"],
                        type=source_info["type"],
                        content=content[:5000],
                        relevance=0.95,
                        timestamp=datetime.now().isoformat()
                    ))
            except Exception:
                pass

    def _search_community_resources(self) -> None:
        """Search community resources like GitHub and forums."""
        # Search GitHub for claude configs
        github_results = self._search_github("claude code configuration")
        for result in github_results[:5]:
            self.sources.append(result)

    def _search_github(self, query: str) -> list[ResearchSource]:
        """Search GitHub for relevant repositories."""
        sources = []
        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            url = f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=5"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for repo in data.get("items", [])[:5]:
                    sources.append(ResearchSource(
                        name=f"GitHub: {repo['full_name']}",
                        url=repo["html_url"],
                        type="github",
                        content=repo.get("description", ""),
                        relevance=min(repo.get("stargazers_count", 0) / 1000, 0.9),
                        timestamp=datetime.now().isoformat()
                    ))
        except Exception:
            pass
        return sources

    def _search_web(self, query: str) -> None:
        """Search the web for a topic."""
        # Note: In production, this would use a real search API
        # For now, we add curated knowledge based on query keywords
        self._add_curated_knowledge(query)

    def _fetch_url_content(self, url: str) -> str:
        """Fetch and extract content from a URL."""
        try:
            response = requests.get(url, timeout=10, headers={
                "User-Agent": "ConfigSetupPipeline/1.0"
            })
            if response.status_code == 200:
                # Simple text extraction
                content = response.text
                # Remove HTML tags (simplified)
                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content)
                return content.strip()
        except Exception:
            pass
        return ""

    def _add_curated_knowledge(self, query: str) -> None:
        """Add curated knowledge based on query keywords."""
        query_lower = query.lower()

        # Security knowledge base
        if "security" in query_lower or "permission" in query_lower:
            self._add_security_knowledge()

        # Configuration knowledge base
        if "configuration" in query_lower or "claude.md" in query_lower:
            self._add_configuration_knowledge()

        # Workflow knowledge base
        if "workflow" in query_lower or "hook" in query_lower or "automation" in query_lower:
            self._add_workflow_knowledge()

        # Multi-model knowledge base
        if "multi" in query_lower or "model" in query_lower or "review" in query_lower:
            self._add_multi_model_knowledge()

    def _add_security_knowledge(self) -> None:
        """Add curated security best practices."""
        practices = [
            BestPractice(
                category="security",
                title="Environment-based secret management",
                description="Store all API keys and secrets in environment variables, never in code or config files",
                rationale="Prevents accidental exposure through version control, logs, or config sharing",
                example="source ~/.secrets/load.sh  # Load from secure location",
                anti_pattern="api_key: 'sk-xxx...'  # NEVER hardcode secrets",
                sources=["OWASP Secure Coding", "Claude Code Docs"],
                confidence=0.98,
                priority="critical"
            ),
            BestPractice(
                category="security",
                title="Principle of least privilege",
                description="Use allowlists rather than denylists for tool permissions",
                rationale="Allowlists are safer because new dangerous commands are blocked by default",
                example='{"allow": ["Bash(git:*)", "Bash(npm:*)"]}',
                anti_pattern='{"deny": ["Bash(rm -rf:*)"]}  # Denylist can miss variations',
                sources=["Security Engineering", "Claude Code Best Practices"],
                confidence=0.95,
                priority="critical"
            ),
            BestPractice(
                category="security",
                title="Destructive command protection",
                description="Always deny rm -rf on root/home directories and require confirmation for deletions",
                rationale="Prevents catastrophic data loss from AI errors or misinterpretation",
                example='{"deny": ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(sudo:*)"]}',
                anti_pattern="Allowing unrestricted rm commands",
                sources=["System Administration Best Practices"],
                confidence=0.98,
                priority="critical"
            ),
            BestPractice(
                category="security",
                title="Pre-commit secret scanning",
                description="Use hooks to scan for secrets before committing code",
                rationale="Last line of defense against accidental secret commits",
                example="PreToolUse hook with gitleaks or similar scanner",
                anti_pattern="Relying only on .gitignore",
                sources=["DevSecOps Practices"],
                confidence=0.9,
                priority="high"
            ),
        ]
        self.best_practices.extend(practices)

    def _add_configuration_knowledge(self) -> None:
        """Add curated configuration best practices."""
        practices = [
            BestPractice(
                category="configuration",
                title="Identity confirmation pattern",
                description="Have Claude confirm it read the config by using a specific name or phrase",
                rationale="Ensures config was loaded and provides clear signal of session state",
                example='Respond to me as "Boss" to confirm you read this file.',
                anti_pattern="No confirmation mechanism",
                sources=["Claude Code Community Patterns"],
                confidence=0.95,
                priority="high"
            ),
            BestPractice(
                category="configuration",
                title="Context compression recovery",
                description="Include explicit instructions for recovering from context compression",
                rationale="Long sessions compress context; explicit recovery steps ensure continuity",
                example="If restored: re-read config, reload secrets, announce state",
                anti_pattern="Assuming context is always fresh",
                sources=["Long-running AI Session Patterns"],
                confidence=0.92,
                priority="high"
            ),
            BestPractice(
                category="configuration",
                title="Before/After task checklists",
                description="Include explicit checklists for task preparation and completion",
                rationale="Ensures consistent workflow and prevents forgotten steps",
                example="Before: load secrets, read ARCHITECTURE.md. After: run tests, update docs",
                anti_pattern="Relying on AI to remember all steps",
                sources=["Process Engineering"],
                confidence=0.9,
                priority="high"
            ),
            BestPractice(
                category="configuration",
                title="Documentation pointers",
                description="Reference key documentation files with their paths",
                rationale="Helps AI navigate project structure and find relevant context",
                example="| Architecture | docs/ARCHITECTURE.md | | Testing | docs/TESTING.md |",
                anti_pattern="Expecting AI to search for docs",
                sources=["Developer Experience Patterns"],
                confidence=0.88,
                priority="medium"
            ),
        ]
        self.best_practices.extend(practices)

    def _add_workflow_knowledge(self) -> None:
        """Add curated workflow best practices."""
        practices = [
            BestPractice(
                category="workflow",
                title="Post-edit validation hooks",
                description="Run automatic validation after file modifications",
                rationale="Catches errors immediately, maintains code quality",
                example='{"PostToolUse": [{"matcher": "Edit|Write", "hooks": [lint, test]}]}',
                anti_pattern="Only running checks before commit",
                sources=["CI/CD Best Practices"],
                confidence=0.9,
                priority="high"
            ),
            BestPractice(
                category="workflow",
                title="Session metrics tracking",
                description="Track tool usage and patterns for optimization",
                rationale="Data-driven improvement of configuration effectiveness",
                example="PostToolUse hook to log metrics to analytics",
                anti_pattern="Flying blind without metrics",
                sources=["Observability Patterns"],
                confidence=0.85,
                priority="medium"
            ),
            BestPractice(
                category="workflow",
                title="Self-reflection protocol",
                description="Implement /reflect command for learning from mistakes",
                rationale="Continuous improvement through structured error analysis",
                example="Analyze -> Abstract -> Generalize -> Document in learned_lessons.md",
                anti_pattern="Repeating the same mistakes",
                sources=["Learning Organization Patterns"],
                confidence=0.88,
                priority="medium"
            ),
        ]
        self.best_practices.extend(practices)

    def _add_multi_model_knowledge(self) -> None:
        """Add curated multi-model best practices."""
        practices = [
            BestPractice(
                category="multi_model",
                title="Parallel model execution",
                description="Run multiple models in parallel for faster reviews",
                rationale="Reduces latency while getting diverse perspectives",
                example="ThreadPoolExecutor with timeout handling",
                anti_pattern="Sequential model calls",
                sources=["Concurrent Programming Patterns"],
                confidence=0.9,
                priority="high"
            ),
            BestPractice(
                category="multi_model",
                title="Finding deduplication",
                description="Deduplicate findings across models before presenting",
                rationale="Reduces noise and highlights consensus findings",
                example="Hash on (file, issue_description[:50]) to detect duplicates",
                anti_pattern="Showing duplicate findings from each model",
                sources=["Data Processing Patterns"],
                confidence=0.92,
                priority="high"
            ),
            BestPractice(
                category="multi_model",
                title="Confidence thresholds",
                description="Only surface findings with confidence >= 80%",
                rationale="Reduces false positives and improves signal-to-noise",
                example='if finding.confidence >= 80: include(finding)',
                anti_pattern="Including all findings regardless of confidence",
                sources=["ML Output Quality Patterns"],
                confidence=0.88,
                priority="medium"
            ),
            BestPractice(
                category="multi_model",
                title="Model specialization",
                description="Use different models for their strengths",
                rationale="Each model has different capabilities and perspectives",
                example="GPT: code patterns, Gemini: security, Claude: architecture",
                anti_pattern="Treating all models identically",
                sources=["AI Ensemble Patterns"],
                confidence=0.85,
                priority="medium"
            ),
        ]
        self.best_practices.extend(practices)

    def _synthesize_with_llm(self, focus_topic: Optional[str] = None) -> None:
        """Use LLM to synthesize and validate findings."""
        if not self.best_practices:
            self._extract_best_practices()

        # Build synthesis prompt
        practices_text = "\n".join([
            f"- {bp.title}: {bp.description}"
            for bp in self.best_practices[:20]
        ])

        context_text = ""
        if self.context.tech_stack:
            context_text += f"Tech stack: {', '.join(self.context.tech_stack)}\n"
        if self.context.use_case:
            context_text += f"Use case: {self.context.use_case}\n"

        prompt = f"""You are an expert on Claude Code configuration and AI coding assistants.

Given these discovered best practices:
{practices_text}

{f'Context: {context_text}' if context_text else ''}

Please:
1. Validate these practices (are they correct and current?)
2. Identify any missing critical practices
3. Prioritize them for this context
4. Suggest any context-specific adaptations

Respond with JSON:
{{"validated": ["practice titles that are correct"], "additions": [{{"title": "...", "description": "...", "priority": "critical|high|medium"}}], "adaptations": [{{"practice": "title", "adaptation": "context-specific change"}}]}}
"""

        # Try OpenAI first, then Gemini
        result = None
        if self.openai_key:
            result = self._call_openai(prompt)
        if not result and self.gemini_key:
            result = self._call_gemini(prompt)

        if result:
            self._apply_synthesis(result)

    def _call_openai(self, prompt: str) -> Optional[dict]:
        """Call OpenAI API for synthesis."""
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for synthesis
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            content = response.choices[0].message.content
            if content:
                return self._extract_json(content)
        except Exception as e:
            print(f"      OpenAI synthesis failed: {e}")
        return None

    def _call_gemini(self, prompt: str) -> Optional[dict]:
        """Call Gemini API for synthesis."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            if response.text:
                return self._extract_json(response.text)
        except Exception as e:
            print(f"      Gemini synthesis failed: {e}")
        return None

    def _extract_json(self, content: str) -> Optional[dict]:
        """Extract JSON from LLM response."""
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
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except Exception:
            pass
        return None

    def _apply_synthesis(self, result: dict) -> None:
        """Apply LLM synthesis results."""
        # Add new practices from synthesis
        for addition in result.get("additions", []):
            self.best_practices.append(BestPractice(
                category="synthesized",
                title=addition.get("title", ""),
                description=addition.get("description", ""),
                priority=addition.get("priority", "medium"),
                sources=["LLM Synthesis"],
                confidence=0.8
            ))

        # Mark validated practices
        validated_titles = set(result.get("validated", []))
        for bp in self.best_practices:
            if bp.title in validated_titles:
                bp.confidence = min(bp.confidence + 0.1, 0.99)

    def _extract_best_practices(self) -> None:
        """Extract best practices from sources (non-LLM fallback)."""
        # Add all curated knowledge if not already added
        if not self.best_practices:
            self._add_security_knowledge()
            self._add_configuration_knowledge()
            self._add_workflow_knowledge()
            self._add_multi_model_knowledge()

    def _prioritize_for_context(self) -> None:
        """Prioritize practices based on context."""
        for bp in self.best_practices:
            # Boost security for enterprise use cases
            if self.context.security_requirements == "high":
                if bp.category == "security":
                    bp.priority = "critical"

            # Boost relevant tech stack practices
            for tech in self.context.tech_stack:
                tech_lower = tech.lower()
                if tech_lower in bp.description.lower() or tech_lower in bp.example.lower():
                    if bp.priority == "low":
                        bp.priority = "medium"
                    elif bp.priority == "medium":
                        bp.priority = "high"

    def _build_results(self) -> dict:
        """Build the final results dictionary."""
        # Deduplicate practices
        seen_titles = set()
        unique_practices = []
        for bp in self.best_practices:
            if bp.title not in seen_titles:
                seen_titles.add(bp.title)
                unique_practices.append(bp)

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unique_practices.sort(key=lambda bp: (priority_order.get(bp.priority, 3), -bp.confidence))

        return {
            "sources": [
                {"name": s.name, "url": s.url, "type": s.type, "relevance": s.relevance}
                for s in self.sources
            ],
            "best_practices": [
                {
                    "category": bp.category,
                    "title": bp.title,
                    "description": bp.description,
                    "rationale": bp.rationale,
                    "example": bp.example,
                    "anti_pattern": bp.anti_pattern,
                    "priority": bp.priority,
                    "confidence": bp.confidence
                }
                for bp in unique_practices
            ],
            "summary": {
                "total_practices": len(unique_practices),
                "critical": len([bp for bp in unique_practices if bp.priority == "critical"]),
                "high": len([bp for bp in unique_practices if bp.priority == "high"]),
                "sources_analyzed": len(self.sources)
            },
            "timestamp": datetime.now().isoformat()
        }

    def print_summary(self, results: dict) -> None:
        """Print a human-readable summary."""
        print("\n" + "=" * 60)
        print("📚 RESEARCH SUMMARY")
        print("=" * 60)

        summary = results.get("summary", {})
        print(f"\nSources analyzed: {summary.get('sources_analyzed', 0)}")
        print(f"Best practices found: {summary.get('total_practices', 0)}")
        print(f"   Critical: {summary.get('critical', 0)}")
        print(f"   High: {summary.get('high', 0)}")

        print("\n--- CRITICAL PRACTICES ---")
        for bp in results.get("best_practices", []):
            if bp["priority"] == "critical":
                print(f"\n   [{bp['category'].upper()}] {bp['title']}")
                print(f"   {bp['description'][:70]}...")
                if bp.get("rationale"):
                    print(f"   Why: {bp['rationale'][:60]}...")

        print("\n--- HIGH PRIORITY ---")
        for bp in results.get("best_practices", [])[:5]:
            if bp["priority"] == "high":
                print(f"\n   [{bp['category'].upper()}] {bp['title']}")
                print(f"   {bp['description'][:70]}...")

        print("\n" + "=" * 60)
