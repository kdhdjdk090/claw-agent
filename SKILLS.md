# Claw Agent — Skills Catalog

All built-in skills and how they work. Skills are predefined expertise modes.

## Built-in Skills (18+)

### 🔧 Core Engineering

| Skill | Version | Description |
|-------|---------|-------------|
| `code` | 1.0.0 | Write, edit, and generate code in any language |
| `debug` | 1.0.0 | Systematic bug diagnosis and fixing |
| `refactor` | 1.0.0 | Restructure code without changing behavior |
| `review` | 1.0.0 | Code review with security, performance, and style checks |
| `test` | 1.0.0 | Write unit tests, integration tests, E2E tests |
| `docs` | 1.0.0 | Generate documentation, READMEs, API docs |
| `design` | 1.0.0 | Architecture design, system design, API design |

### 📊 Analysis & Research

| Skill | Version | Description |
|-------|---------|-------------|
| `analyze` | 1.0.0 | Analyze code, data, logs, or any structured content |
| `search` | 1.0.0 | Deep web and codebase research |
| `extract` | 1.0.0 | Pull structured data from unstructured sources |
| `vision` | 1.0.0 | Analyze images, screenshots, diagrams |

### 📝 Content & Communication

| Skill | Version | Description |
|-------|---------|-------------|
| `write` | 1.0.0 | General writing — articles, emails, docs |
| `summarize` | 1.0.0 | Condense long content into key points |
| `translate` | 1.0.0 | Translate between natural languages |
| `explain` | 1.0.0 | Explain complex concepts simply |

### 🧠 Thinking & Problem Solving

| Skill | Version | Description |
|-------|---------|-------------|
| `reason` | 2.0.0 | Formal reasoning with 8-patch engine (includes PATCH 8 feasibility checker) |
| `math` | 1.0.0 | Mathematical computation and proofs |
| `brainstorm` | 1.0.0 | Creative ideation and option exploration |

## Skill Architecture

### How Skills Work
```
User message → Skill Detection → Skill Context Injection → LLM Call → Response
```

1. **Detection**: The agent analyzes the user's message to determine which skill is most relevant
2. **Context Injection**: The skill's system prompt additions are prepended to the request
3. **Execution**: The LLM receives the skill-enhanced prompt and generates a response
4. **Output**: Response is formatted according to the skill's output rules

### Skill Definition (SkillInfo)
```python
@dataclass
class SkillInfo:
    name: str           # Unique identifier
    display_name: str   # Human-readable name
    description: str    # What the skill does
    system_prompt: str  # Additional instructions for LLM
    version: str        # Semantic version
    tags: list[str]     # Categories for discovery
    builtin: bool       # True = ships with Claw
```

### Custom Skills
Users can add custom skills via:
- `install_skill(skill_info)` — Add to runtime registry
- `uninstall_skill(name)` — Remove from registry
- Skills persist across sessions if saved to config

## Skill Selection Guide

| User Intent | Skill | Key Indicators |
|---|---|---|
| "Fix this bug" | `debug` | error, bug, broken, fails, crash |
| "Write a function" | `code` | create, implement, build, make |
| "Clean up this code" | `refactor` | refactor, clean, reorganize, simplify |
| "Is this code good?" | `review` | review, check, audit, evaluate |
| "Write tests" | `test` | test, spec, coverage, assert |
| "Explain how X works" | `explain` | explain, how, why, what does |
| "Prove this" | `reason` | prove, impossible, therefore, logically |
| "Calculate X" | `math` | calculate, compute, solve, equation |
| "Research X" | `search` | find, research, look up, what is |
| "Summarize this" | `summarize` | summarize, TL;DR, key points, brief |
| "Write an article" | `write` | write, draft, compose, article |
| "Design the system" | `design` | design, architect, structure, plan |

## The `reason` Skill (v2.0.0)

The most sophisticated skill, powered by the full AI Lab:

### Capabilities
- Formal logical proofs (propositional, predicate, modal logic)
- Information-theoretic impossibility proofs
- Mathematical computation with verification
- Constraint satisfaction checking (PATCH 8)
- Multi-step reasoning with assumption tracking
- Adversarial self-testing via Solver/Judge protocol

### When It Activates
- Problem requires proof or formal verification
- Mathematical or logical problem
- "Is this possible?" type questions
- Requires reasoning beyond pattern matching

### Verdict Scale
Outputs from the reasoning engine are graded:
```
AMATEUR (< 20%)  → Fundamentally flawed
COMPETENT (20-50%) → Basic approach correct, issues present
SKILLED (50-75%) → Solid solution, minor improvements possible
EXPERT (75-90%) → Excellent solution, edge cases handled
ELITE (90-100%) → Provably correct, comprehensive, publishable
```

## Adding New Skills

To add a skill to Claw Agent:

1. Define the `SkillInfo`:
```python
new_skill = SkillInfo(
    name="my_skill",
    display_name="My Custom Skill",
    description="What it does",
    system_prompt="Additional LLM instructions for this skill",
    version="1.0.0",
    tags=["custom", "domain"],
    builtin=False
)
```

2. Register it:
```python
from claw_agent.skills import install_skill
install_skill(new_skill)
```

3. The skill will now be available for automatic or manual selection.
