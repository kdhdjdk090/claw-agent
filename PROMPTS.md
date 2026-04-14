# Claw Agent — Prompt Engineering Reference

Templates and patterns for system prompts, skill prompts, and response generation.

## System Prompt Assembly (6 Layers)

The system prompt is assembled in `Agent.__init__()` by stacking these layers:

```
Layer 1: SYSTEM_PROMPT_TEMPLATE    — Identity, tools, rules, formatting
Layer 2: _load_project_context()   — MEMORY.md + SOUL.md + .claw (4K cap each)
Layer 3: get_all_skills_context()  — Custom skill definitions (non-builtin only)
Layer 4: REASONING_WISDOM          — Arena.py's best practices from Solver/Judge
Layer 5: SEAKS kernel patch        — Dynamic rules from self-evolving kernel
Layer 6: MCP context               — External tool server descriptions
```

### Layer Priority
- Later layers override earlier layers for conflicting instructions
- SEAKS kernel (Layer 5) can override any static rule if it learns something better
- Project context (Layer 2) provides workspace-specific overrides

## Prompt Templates

### Skill Prompt Template
```
You are executing the "{skill_name}" skill.

## Task
{user_request}

## Constraints
- {constraint_1}
- {constraint_2}

## Output Format
{expected_format}
```

### Code Generation Template
```
Write {language} code that {description}.

Requirements:
- {requirement_1}
- {requirement_2}

Context:
- Project uses {framework}
- Existing patterns: {patterns}
- File location: {path}
```

### Bug Analysis Template
```
Analyze this error:

```
{error_message}
```

The error occurs in {file}:{line}.
The function is supposed to {expected_behavior}.
Instead it {actual_behavior}.

Provide: root cause, fix (as code), and explanation.
```

### Code Review Template
```
Review this code change:

```diff
{diff}
```

Check for:
1. Correctness — does it do what it claims?
2. Security — input validation, injection, auth
3. Performance — unnecessary work, N+1, allocations
4. Style — naming, structure, readability
5. Edge cases — nulls, empty inputs, boundaries

Format: Critical / Warning / Suggestion with line references.
```

### Refactoring Template
```
Refactor {target} in {file}.

Current issues:
- {issue_1}
- {issue_2}

Goals:
- {goal_1}
- {goal_2}

Constraints:
- Don't change the public API
- All existing tests must pass
- Follow existing code conventions
```

## Prompt Engineering Rules

### 1. Be Specific Over General
❌ "Write good code"
✅ "Write a Python function that parses CSV with headers, handles quoted commas, and returns list of dicts"

### 2. Include Format Instructions
❌ "Explain the architecture"
✅ "Explain the architecture. Use a bullet list for components and a table for their interactions."

### 3. Provide Context
❌ "Fix the auth bug"
✅ "Fix the auth bug in `middleware/auth.py`. JWT tokens expire but the refresh logic in `refresh_token()` doesn't update the session store."

### 4. Constrain Output
❌ "Help me with this"
✅ "Identify the top 3 performance issues in this function. For each: state the issue, estimate impact, provide a fix."

### 5. Chain of Thought Triggers
When you need the agent to think through a problem:
- "Think step by step"
- "Before answering, list your assumptions"
- "Show your reasoning"
- "What could go wrong?"

## Council Prompt Patterns

### Consensus Question
```
{question}

Think independently. Provide your answer with confidence score (0.0-1.0).
Do NOT try to guess what other models might say.
```

### Adversarial Review
```
A previous model suggested: {solution}

Play devil's advocate. Find the weaknesses in this approach.
What edge cases does it miss? What could go wrong in production?
```

### Tie-Breaking
```
Two approaches were suggested:
A: {approach_a}
B: {approach_b}

Choose one. Justify with: correctness, simplicity, and maintainability.
State your confidence.
```

## Response Quality Checklist

Before sending any response, verify:
- [ ] Directly answers the user's question (not tangential)
- [ ] Code blocks have language tags
- [ ] No raw escape sequences or control characters
- [ ] No hallucinated file paths, function names, or APIs
- [ ] Claims are backed by tool output (not memory)
- [ ] Formatting is clean markdown (headers, lists, code blocks)
- [ ] Response length matches complexity (not bloated, not terse)
