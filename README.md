# Config Setup Pipeline

🚀 **Generate exceptional Claude Code configurations with AI-powered analysis.**

A powerful tool that helps anyone create optimized Claude Code configurations through:
- **Deep research** on best practices with LLM synthesis
- **Critical analysis** that questions your choices
- **Learning** from your existing configurations
- **Multi-model review** (GPT-5.2 + Gemini 3)
- **Comprehensive validation** before deployment

## Why This Exists

Setting up Claude Code configurations can be overwhelming. There are dozens of options, security considerations, and best practices to follow. This tool automates the entire process while ensuring you end up with a configuration that's:

- **Secure** - Follows security best practices
- **Effective** - Optimized for your specific workflow
- **Validated** - Reviewed by multiple AI models
- **Consistent** - Learns from your existing patterns

## Quick Start

```bash
# Install
pip install -e .

# First-time setup (API keys, preferences)
python -m src.main --setup-keys

# Generate a configuration
python -m src.main

# Quick mode (fewer questions, sensible defaults)
python -m src.main --quick
```

## Features

### 🔑 API Key Management

Secure storage for your API keys with validation:

```bash
# Interactive API key setup
python -m src.main --setup-keys

# Check current status
python -m src.main status
```

Supports:
- OpenAI (GPT-5.2 for code review)
- Google Gemini (Gemini 3 Pro)
- Anthropic (optional Claude model)

Keys are stored securely in `~/.config/config-setup-pipeline/.env` with restricted permissions.

### 📊 Learn from Existing Configs

Automatically discovers and analyzes your existing Claude configurations:

```bash
# Analyze configs in default location
python -m src.main analyze

# Analyze specific path
python -m src.main analyze ~/my-projects

# Output as JSON
python -m src.main analyze --json
```

Extracts:
- Agent patterns and definitions
- Command definitions
- Hook configurations
- Permission patterns
- Best practices you already follow

### 🔍 Deep Research

Researches latest Claude Code best practices from multiple sources:

```bash
# Full research
python -m src.main research

# Research specific topic
python -m src.main research --topic security

# Research for your tech stack
python -m src.main research --stack "Python,FastAPI,PostgreSQL"
```

Sources include:
- Official Claude Code documentation
- GitHub community configurations
- LLM-powered synthesis of findings

### 🤔 Critical Advisor

Questions your choices and identifies potential issues:

- **Security Analysis** - Flags risky permission combinations
- **Coherence Checks** - Ensures features work well together
- **Best Practice Alignment** - Compares against researched patterns
- **Missing Essentials** - Identifies important missing components

### ✅ Comprehensive Validation

Validates generated configurations before writing:

```bash
# Validate existing config
python -m src.main validate ./my-config
```

Checks:
- Syntax and structure correctness
- Security best practices compliance
- No hardcoded secrets
- Required patterns present
- Cross-file reference integrity

### 🔬 Multi-Model Review

Uses multiple AI models to review your configuration:

```bash
# Review existing config
python -m src.main review ./my-config
```

Models analyze for:
- Security vulnerabilities
- Best practice violations
- Missing components
- Improvement opportunities

## Generated Configuration

The pipeline generates a complete Claude Code setup:

```
my-config/
├── CLAUDE.md                 # Main configuration with:
│   ├── Identity confirmation
│   ├── Context recovery instructions
│   ├── Tech stack documentation
│   ├── Before/After task checklists
│   └── Documentation pointers
│
├── models.json               # Multi-model settings
│
├── .claude/
│   ├── settings.json         # Permissions & hooks
│   ├── agents/               # Specialized agents
│   │   ├── code-reviewer.md
│   │   ├── architect.md
│   │   ├── debugger.md
│   │   └── security-auditor.md
│   ├── commands/             # Slash commands
│   │   ├── reflect.md
│   │   ├── review.md
│   │   └── check.md
│   └── rules/
│       ├── learned_lessons.md
│       └── safety.md
│
└── docs/memory/              # Persistent memory system
    ├── session_log.md
    ├── mistakes.md
    ├── decisions.md
    └── discoveries.md
```

## Configuration Options

The interactive questionnaire covers:

### Basics
- Configuration name and identity phrase
- Purpose (solo, team, enterprise, learning, research)

### Tech Stack
- Primary language
- Frameworks
- Package manager
- Database

### Workflow
- Autonomy level (co-founder, senior dev, assistant)
- Common tasks
- Test runner and build commands

### Security
- Security level (relaxed, standard, high, maximum)
- File deletion policies
- Shell command allowlists

### Features
- Hooks (post-edit validation, metrics, reflection)
- Memory system for persistent learning
- Specialized agents
- Slash commands

### Multi-Model
- Model selection (GPT-5.2, Gemini 3, Claude)
- OptILLM optimization techniques

## Commands Reference

| Command | Description |
|---------|-------------|
| `python -m src.main` | Full interactive setup |
| `python -m src.main --quick` | Quick setup with defaults |
| `python -m src.main --setup-keys` | Configure API keys |
| `python -m src.main status` | Show setup status |
| `python -m src.main analyze [path]` | Analyze existing configs |
| `python -m src.main research` | Research best practices |
| `python -m src.main review <path>` | Review a configuration |
| `python -m src.main validate <path>` | Validate a configuration |

## Architecture

```
src/
├── main.py                   # CLI entry point
├── setup/                    # First-time setup
│   ├── wizard.py             # Setup wizard
│   └── api_keys.py           # API key management
├── questions/                # Interactive questionnaire
│   └── engine.py             # Question engine
├── research/                 # Best practices research
│   └── researcher.py         # Multi-source researcher
├── analyzer/                 # Config analysis
│   └── config_analyzer.py    # Pattern extraction
├── generator/                # Config generation
│   └── config_generator.py   # Template-based generator
├── advisor/                  # Critical analysis
│   └── critical_advisor.py   # Assumption questioning
├── validator/                # Validation
│   └── config_validator.py   # Comprehensive checks
└── review/                   # Multi-model review
    └── reviewer.py           # GPT-5.2 + Gemini review
```

## Best Practices Included

The generated configurations follow these researched best practices:

### Security (Critical)
- Environment-based secret management
- Principle of least privilege (allowlists)
- Destructive command protection
- Pre-commit secret scanning

### Configuration (High Priority)
- Identity confirmation pattern
- Context compression recovery
- Before/After task checklists
- Documentation pointers

### Workflow (High Priority)
- Post-edit validation hooks
- Session metrics tracking
- Self-reflection protocol

### Multi-Model (Medium Priority)
- Parallel model execution
- Finding deduplication
- Confidence thresholds
- Model specialization

## Environment Variables

For full functionality, set these API keys:

```bash
export OPENAI_API_KEY="sk-..."      # For GPT-5.2 Codex
export GEMINI_API_KEY="..."         # For Gemini 3 Pro
export ANTHROPIC_API_KEY="sk-..."   # Optional: For Claude
```

Or use the built-in key manager:
```bash
python -m src.main --setup-keys
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run validation: `python -m src.main validate .`
5. Submit a pull request

## License

MIT License - see LICENSE file.

---

Built with 🤖 by Claude Code

*"The people who are crazy enough to think they can change the world are the ones who do."*
