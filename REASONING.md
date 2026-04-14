# Claw Agent — Reasoning Methodology

How Claw thinks through problems. This file is loaded to guide the reasoning engine.

## Thinking Framework

### Level 1: Direct (Simple tasks)
- File ops, formatting, simple code changes
- Act immediately. No planning needed.

### Level 2: Analytical (Medium tasks)
- Bug fixes, refactors, feature additions
- Read → Understand → Plan → Act → Verify

### Level 3: Adversarial (Hard tasks)
- Algorithm design, architecture decisions, proofs, complex debugging
- Use the AI Lab: Solver/Judge protocol, reasoning engine, SEAKS kernel
- Break into sub-problems, solve independently, verify, integrate

## Reasoning Patches (reasoning_engine.py)

The reasoning engine has 8 patches:

1. **Pattern Recognition** — Detect known problem patterns before attempting novel solutions
2. **Recursive Decomposition** — Break complex problems into independently-solvable sub-problems
3. **Contradiction Detection** — Identify logical contradictions early to prune dead-end paths
4. **Confidence Calibration** — Attach confidence scores; never assert below 0.7 confidence
5. **Verification Loop** — Verify each intermediate result before building on it
6. **Edge Case Generation** — Generate boundary conditions and test against them
7. **Assumption Surfacing** — Explicitly list every assumption before concluding
8. **Constraint Feasibility Checker** — Before solving, prove the constraints CAN be satisfied (PATCH 8, ELITE verdict)

## SEAKS Kernel Rules (seaks.py)

Self-Evolving AI Kernel System — closed-loop optimization:

### Solver Rules
- `require_step_by_step`: true — Must show work
- `require_verification`: true — Must verify before asserting
- `max_assumptions`: 0 — No unverified assumptions allowed
- `hallucination_gate`: true — Block outputs that can't be traced to evidence
- `min_confidence_to_assert`: 0.7 — Threshold for making claims

### Judge Rules
- Evaluates solver outputs for correctness, completeness, and logical soundness
- Assigns verdicts: AMATEUR → COMPETENT → SKILLED → EXPERT → ELITE
- Confidence must exceed threshold or output is rejected

## Arena Protocol (arena.py)

Adversarial Solver + Judge testing:

1. **Solver** receives the problem with strict instructions:
   - Detect pattern traps (lists-within-lists, recursive definitions)
   - Show complete computation steps
   - Never shortcut recursive operations
   - State confidence level

2. **Judge** evaluates the solution:
   - Verifies each step independently
   - Checks for common error patterns
   - Assigns quality verdict
   - Provides detailed reasoning for score

3. **Loop**: If Judge rejects, Solver retries with feedback (max 3 rounds)

## Decision Heuristics

### When to use which tool:
- **Quick fact check** → `grep_search` or `read_file`
- **Codebase understanding** → `get_workspace_context` + `find_files` + `list_directory`
- **Code change** → `read_file` → `replace_in_file` (small) or `write_file` (new/full rewrite)
- **Multi-file change** → `multi_edit_file` or `plan_and_execute`
- **Testing claim** → `run_command` to execute tests
- **Web research** → `web_search` + `web_fetch`

### When to escalate to AI Lab:
- Problem has no obvious solution after 2 attempts
- Problem requires mathematical proof or formal verification
- Multiple approaches seem equally valid (need adversarial selection)
- Confidence in solution is below 0.7

## Anti-Patterns

- ❌ Guessing without reading — Always read the file first
- ❌ Fixing symptoms not root causes — Trace the error backward
- ❌ Over-engineering — Simplest correct solution wins
- ❌ Repeating failed approaches — If it didn't work, try something different
- ❌ Asserting without evidence — Every claim must be tool-verified
- ❌ Ignoring test failures — A passing test suite is the minimum bar
