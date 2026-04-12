"""Sub-agent tool — spawn focused sub-agents for specific tasks."""

from __future__ import annotations

import json
from typing import Any

import httpx


def run_subagent(
    task: str,
    tools_subset: str = "all",
    model: str | None = None,
    max_iterations: int = 5,
) -> str:
    """Spawn a focused sub-agent for a specific task.
    
    The sub-agent gets its own conversation context and tool access,
    runs independently, and returns a summary of what it accomplished.
    
    tools_subset: "all", "read_only", "file_only", or comma-separated tool names
    max_iterations: cap on agent loop iterations (default 5 for focused work)
    """
    from ..agent import Agent, MAX_ITERATIONS as _DEFAULT_MAX
    from ..permissions import PermissionContext, ALWAYS_ALLOWED

    # Use the current agent's model if not specified, fall back to a smaller model
    agent_model = model or "qwen2.5:7b"

    # Build permission context based on tools_subset
    perms = PermissionContext.default()
    if tools_subset == "read_only":
        # Block all write/execute tools
        perms = PermissionContext(deny_names=frozenset({
            "write_file", "replace_in_file", "multi_edit_file", "insert_at_line",
            "run_command", "powershell", "notebook_run",
        }))
    elif tools_subset == "file_only":
        perms = PermissionContext(deny_names=frozenset({
            "run_command", "powershell", "web_fetch", "web_search",
            "run_subagent", "plan_and_execute", "notebook_run",
        }))
    elif tools_subset != "all":
        # Comma-separated allowlist — deny everything not listed
        allowed = set(t.strip() for t in tools_subset.split(",") if t.strip())
        from ..tools import TOOL_REGISTRY
        deny = frozenset(name for name in TOOL_REGISTRY if name not in allowed)
        perms = PermissionContext(deny_names=deny)

    # Always auto-approve for sub-agents (they don't have user interaction)
    perms.auto_approve = True

    sub = Agent(model=agent_model, permissions=perms)

    # Override max iterations for sub-agents via monkey-patch on the loop
    import claw_agent.agent as _agent_module
    original_max = _agent_module.MAX_ITERATIONS
    _agent_module.MAX_ITERATIONS = min(max_iterations, 50)  # cap at 50

    try:
        result = sub.chat(
            f"You are a focused sub-agent. Complete this specific task and return a clear summary:\n\n{task}"
        )
        return f"[Sub-agent completed]\n{result}"
    except Exception as e:
        return f"[Sub-agent error] {e}"
    finally:
        _agent_module.MAX_ITERATIONS = original_max


def plan_and_execute(goal: str, model: str | None = None) -> str:
    """Break a goal into steps, then execute each with a sub-agent."""
    from ..agent import Agent

    agent_model = model or "qwen2.5:7b"
    planner = Agent(model=agent_model)

    # Step 1: Plan
    plan = planner.chat(
        f"Break this goal into 3-5 concrete, actionable steps. "
        f"Return ONLY a numbered list of steps, nothing else:\n\n{goal}"
    )

    results = [f"Plan:\n{plan}\n\nExecution:"]

    # Step 2: Execute each step
    lines = [l.strip() for l in plan.split("\n") if l.strip() and l.strip()[0].isdigit()]

    for i, step in enumerate(lines[:5], 1):
        # Clean the step text
        step_text = step.lstrip("0123456789.) ").strip()
        if not step_text:
            continue

        results.append(f"\n--- Step {i}: {step_text} ---")
        step_result = run_subagent(step_text, model=model)
        results.append(step_result)

    return "\n".join(results)
