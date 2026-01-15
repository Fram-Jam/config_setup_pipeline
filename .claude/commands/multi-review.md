---
description: Run multi-model review with GPT-5.2 and Gemini 3 (REQUIRED before push)
---

# Multi-Model Review Protocol

You MUST run this after /review passes. This provides a second layer of verification using external models.

## Instructions

1. Load API keys:
   ```bash
   source ~/.secrets/load.sh
   ```

2. Gather all Python source files from `src/` (excluding __pycache__)

3. Query BOTH models in parallel with this prompt:
   ```
   You are an expert code reviewer. Analyze this Python codebase for:
   1. Critical bugs - Runtime errors, logic errors, crashes
   2. Security vulnerabilities - Injection, traversal, secrets
   3. Type safety issues - Wrong types, missing validation
   4. Architecture problems - Inconsistent contracts, duplicates
   
   Return ONLY a JSON object:
   {"issues": [{"severity": "critical|high|medium|low", "file": "path", "line": N, "message": "description", "fix": "suggestion"}]}
   
   Only include issues with high confidence (>80%).
   ```

4. Use these model configurations:
   - **GPT-5.2**: `gpt-5.2-chat-latest` via chat completions, `max_completion_tokens=4096`
   - **Gemini 3**: `gemini-3-pro-preview` via generate_content, `temperature=0.1`

5. Combine and deduplicate findings from both models

6. Present findings:
   | Model | Severity | File:Line | Issue | Fix |
   |-------|----------|-----------|-------|-----|

7. Verdict:
   - If ANY critical or high issues from EITHER model:
     "❌ MULTI-MODEL REVIEW FAILED - Fix issues and run /multi-review again"
   - If BOTH models find no critical/high issues:
     "✅ MULTI-MODEL REVIEW PASSED - Safe to push"

## Acceptance Criteria

- GPT-5.2: Zero critical, zero high
- Gemini 3: Zero critical, zero high
- Consensus required from both models

## After Both Reviews Pass

Only after BOTH /review AND /multi-review pass can you run:
```bash
git push origin main
```

Execute the multi-model review now.
