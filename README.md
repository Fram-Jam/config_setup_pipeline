# Config Setup Pipeline

🚀 **Automated Claude Code configuration generator with multi-model review.**

Generate optimized Claude Code configurations through:
- **Interactive questionnaire** - Answer questions about your workflow
- **Deep research** - Automatically research latest best practices
- **Pattern learning** - Learn from your existing configurations
- **Multi-model review** - GPT-5.2 + Gemini 3 review your generated config

## Features

| Feature | Description |
|---------|-------------|
| 🎯 **Interactive Setup** | Guided questionnaire covering security, workflow, tech stack |
| 🔍 **Best Practices Research** | Researches latest Claude Code patterns and recommendations |
| 📊 **Config Analysis** | Learns from your existing configurations to maintain consistency |
| 🤖 **Multi-Model Review** | GPT-5.2 Codex + Gemini 3 Pro review generated configs |
| 📦 **Complete Generation** | Generates CLAUDE.md, settings.json, agents, commands, memory system |

## Installation

```bash
# Clone the repository
git clone https://github.com/Fram-Jam/config_setup_pipeline.git
cd config_setup_pipeline

# Install dependencies
pip install -e .

# Or install directly
pip install -r requirements.txt
```

## Quick Start

```bash
# Run interactive setup
python -m src.main

# Quick setup with defaults
python -m src.main --quick

# Skip research (faster)
python -m src.main --skip-research

# Skip multi-model review
python -m src.main --skip-review
```

## Commands

### Interactive Setup

```bash
# Full interactive setup
python -m src.main

# Specify output directory
python -m src.main --output ./my-config

# Use existing configs as reference
python -m src.main --configs-path ~/my-claude-configs
```

### Analyze Existing Configs

```bash
# Analyze and extract patterns
python -m src.main analyze

# Output as JSON
python -m src.main analyze --json
```

### Research Best Practices

```bash
# Research all topics
python -m src.main research

# Research specific topic
python -m src.main research --topic "security"
```

### Review a Configuration

```bash
# Review existing config
python -m src.main review ./path/to/config

# Output as JSON
python -m src.main review ./path/to/config --json
```

## Configuration Options

The questionnaire covers:

### Basics
- Configuration name and identity
- Purpose (solo dev, team, enterprise, etc.)

### Tech Stack
- Primary language (Python, TypeScript, Go, etc.)
- Frameworks
- Package manager
- Database

### Workflow
- Autonomy level (co-founder, senior dev, assistant)
- Common tasks
- Test runner and build commands

### Security
- Permission levels
- File deletion policies
- Shell command allowlists

### Features
- Hooks (post-edit, pre-commit, metrics)
- Memory system
- Agents (code reviewer, architect, debugger)
- Commands (/reflect, /review, /standup)

### Multi-Model
- Enable GPT-5.2, Gemini 3, Claude
- OptILLM optimization techniques

## Generated Files

```
my-config/
├── CLAUDE.md              # Main configuration
├── models.json            # Multi-model settings
├── .claude/
│   ├── settings.json      # Permissions & hooks
│   ├── agents/            # Agent definitions
│   │   ├── code-reviewer.md
│   │   └── architect.md
│   ├── commands/          # Slash commands
│   │   ├── reflect.md
│   │   └── review.md
│   └── rules/             # Rules and lessons
│       ├── learned_lessons.md
│       └── safety.md
└── docs/
    └── memory/            # Persistent memory
        ├── session_log.md
        ├── mistakes.md
        ├── decisions.md
        └── discoveries.md
```

## Environment Variables

For multi-model review, set:

```bash
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."
```

Or use a secrets loader:

```bash
source ~/.secrets/load.sh
```

## Architecture

```
src/
├── main.py               # CLI entry point
├── questions/            # Interactive questionnaire
│   └── engine.py         # Question engine
├── research/             # Best practices research
│   └── researcher.py     # Web research
├── analyzer/             # Config pattern extraction
│   └── config_analyzer.py
├── generator/            # Config generation
│   └── config_generator.py
└── review/               # Multi-model review
    └── reviewer.py       # GPT-5.2 + Gemini review
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file.

---

Built with 🤖 by Claude Code
