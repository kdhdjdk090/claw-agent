"""Hook system — pre/post tool execution hooks (ported from Rust crate).

Hooks allow custom logic before and after each tool call.
Configured via ~/.claw-agent/hooks.json or CLAW_HOOKS env var.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HookResult:
    allow: bool = True
    message: str = ""


@dataclass
class HookRunner:
    """Manages pre/post tool execution hooks."""

    hooks: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def load(cls) -> "HookRunner":
        """Load hooks from config file or env var."""
        # Check env var first
        env_hooks = os.environ.get("CLAW_HOOKS")
        if env_hooks:
            try:
                return cls(hooks=json.loads(env_hooks))
            except json.JSONDecodeError:
                pass

        # Check config file
        hooks_path = os.path.join(os.path.expanduser("~"), ".claw-agent", "hooks.json")
        if os.path.exists(hooks_path):
            try:
                with open(hooks_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(hooks=data if isinstance(data, list) else [])
            except (json.JSONDecodeError, OSError):
                pass

        return cls()

    def run_pre_hooks(self, tool_name: str, tool_input: dict) -> HookResult:
        """Run hooks with event=pre_tool_use. Returns allow/deny decision."""
        for hook in self.hooks:
            if hook.get("event") != "pre_tool_use":
                continue
            # Check tool filter
            tool_filter = hook.get("tools")
            if tool_filter and tool_name not in tool_filter:
                continue
            result = self._execute_hook(hook, {
                "event": "pre_tool_use",
                "tool_name": tool_name,
                "tool_input": tool_input,
            })
            if not result.allow:
                return result
        return HookResult(allow=True)

    def run_post_hooks(self, tool_name: str, tool_input: dict, tool_output: str) -> HookResult:
        """Run hooks with event=post_tool_use. Can modify/annotate output."""
        for hook in self.hooks:
            if hook.get("event") != "post_tool_use":
                continue
            tool_filter = hook.get("tools")
            if tool_filter and tool_name not in tool_filter:
                continue
            self._execute_hook(hook, {
                "event": "post_tool_use",
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": tool_output[:2000],
            })
        return HookResult(allow=True)

    def _execute_hook(self, hook: dict, context: dict) -> HookResult:
        """Execute a single hook command with context as JSON stdin."""
        command = hook.get("command")
        if not command:
            return HookResult(allow=True)
        try:
            result = subprocess.run(
                command,
                shell=True,
                input=json.dumps(context),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                msg = result.stderr.strip() or result.stdout.strip()
                return HookResult(allow=False, message=msg or "Hook denied execution")
            return HookResult(allow=True, message=result.stdout.strip())
        except subprocess.TimeoutExpired:
            return HookResult(allow=True, message="Hook timed out (ignored)")
        except Exception:
            return HookResult(allow=True)
