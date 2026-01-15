---
description: Run comprehensive code review (REQUIRED before push)
---

# Code Review Protocol

You MUST run this review before any git push. This is non-negotiable.

## Instructions

1. Use the `code-reviewer` agent to perform a comprehensive review of ALL Python files in `src/`

2. Focus the review on:
   - **Critical bugs** - Runtime errors, logic inversions, type errors
   - **Security** - Path traversal, injection, secrets exposure
   - **Architecture** - Inconsistent contracts, duplicate definitions
   - **Error handling** - Silent exceptions, missing validation
   - **Type safety** - Pydantic model usage, enum consistency

3. Present findings in a clear table:
   | Severity | File:Line | Issue | Fix |
   |----------|-----------|-------|-----|

4. If ANY critical or high issues are found:
   - List them clearly
   - State: "❌ REVIEW FAILED - Fix these issues and run /review again"

5. If NO critical or high issues:
   - State: "✅ CODE REVIEW PASSED - Proceed to /multi-review"

## Acceptance Criteria

- Zero critical issues
- Zero high issues
- All medium issues documented (can defer)

Run the code-reviewer agent now on the entire src/ directory.
