# CLAUDE.md - Config Setup Pipeline

**Address me as "Chief"** - You are building critical infrastructure that others will depend on.

---

## Project Overview

This is the **Config Setup Pipeline** - a tool that generates Claude Code configurations for others. Because our output directly affects the quality of other developers' AI interactions, **zero bugs are acceptable**.

**Tech Stack:** Python 3.9+, Typer CLI, Pydantic 2.x, Rich, OpenAI API, Google Gemini API

---

## MANDATORY: Pre-Push Code Review Protocol

### This is NON-NEGOTIABLE

Before ANY code is pushed to GitHub, it MUST pass:

1. **Code Reviewer Analysis** - Using the `code-reviewer` agent
2. **Multi-Model Review** - GPT-5.2 + Gemini 3 consensus

Both reviews must return **ZERO critical bugs and ZERO high-severity issues** before pushing.

### Review Process

```
┌─────────────────────────────────────────────────────────────┐
│                    PRE-PUSH CHECKLIST                       │
├─────────────────────────────────────────────────────────────┤
│  □ 1. Run code-reviewer agent on all changed files          │
│  □ 2. Fix ALL critical and high issues found                │
│  □ 3. Re-run code-reviewer until clean                      │
│  □ 4. Run multi-model review (GPT-5.2 + Gemini 3)          │
│  □ 5. Fix ALL issues found by either model                  │
│  □ 6. Re-run multi-model review until both pass             │
│  □ 7. Only then: git push                                   │
└─────────────────────────────────────────────────────────────┘
```

### Iteration Requirement

If ANY review finds issues:
- Fix the issues
- Re-run the SAME review that found them
- Continue until that review passes
- Then proceed to next review stage

**There is no "ship it anyway" option. Iterate until clean.**

---

## Code Quality Standards

### Critical (Must Fix Before Push)
- Runtime errors or crashes
- Security vulnerabilities (path traversal, injection, secrets exposure)
- Data loss or corruption risks
- Type errors that would fail at runtime
- Logic inversions (like the dry_run bug we fixed)

### High (Must Fix Before Push)
- Silent exception swallowing
- Missing error handling for user-facing code
- Inconsistent data contracts between modules
- Duplicate/conflicting class definitions

### Medium (Should Fix)
- Code style inconsistencies
- Missing docstrings on public methods
- Deprecated syntax usage

### Low (Can Defer)
- Minor optimizations
- Additional test coverage

---

## Commands

### Before Committing
```bash
# Run code review
/review

# Run multi-model analysis
/multi-review
```

### Development
```bash
# Install dependencies
pip install -e .

# Run the CLI
config-setup --help

# Run tests (when added)
pytest
```

---

## Architecture

```
src/
├── cli.py                  # Typer CLI (primary entry point)
├── main.py                 # Legacy argparse CLI (deprecated)
├── models.py               # Pydantic models + Enums
├── pipeline/               # Pipeline abstraction
│   ├── base.py             # PipelineStage protocol
│   └── stages.py           # Concrete stage implementations
├── setup/                  # First-time setup
├── research/               # Best practices research
├── analyzer/               # Config analysis
├── generator/              # Config generation
├── advisor/                # Critical analysis
├── validator/              # Validation checks
└── review/                 # Multi-model review
```

---

## Before Every Task

1. Read this file completely
2. Understand the review requirements
3. Plan changes carefully to minimize review iterations

## After Every Task

1. Run `/review` - fix all issues
2. Run `/multi-review` - fix all issues  
3. Only then commit and push

---

## Memory

When making significant changes, update:
- `docs/memory/decisions.md` - Architecture decisions
- `docs/memory/mistakes.md` - Bugs found and fixed

---

*"Real artists ship - but only after the code is bulletproof."*
