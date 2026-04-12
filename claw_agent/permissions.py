"""Permission system — gates dangerous tool execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

# Commands/patterns that require explicit user confirmation
DANGEROUS_PATTERNS = (
    "rm -rf",
    "del /s",
    "format ",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",
    "> /dev/sda",
    "shutdown",
    "reboot",
    "git push --force",
    "git reset --hard",
    "drop table",
    "drop database",
    "truncate table",
)

# Tools that are always allowed
ALWAYS_ALLOWED = frozenset({
    "read_file", "list_directory", "find_files", "grep_search",
    "web_search", "web_fetch",
})

# Tools that need confirmation for certain inputs
GATED_TOOLS = frozenset({
    "run_command", "write_file", "replace_in_file",
    "multi_edit_file", "notebook_run",
})


@dataclass
class PermissionContext:
    """Tracks which tools are blocked and permission decisions."""

    deny_names: frozenset[str] = field(default_factory=frozenset)
    deny_prefixes: tuple[str, ...] = ()
    auto_approve: bool = False  # if True, skip all confirmations
    denials: list[dict] = field(default_factory=list)
    approvals: list[str] = field(default_factory=list)

    @classmethod
    def default(cls) -> "PermissionContext":
        return cls()

    @classmethod
    def permissive(cls) -> "PermissionContext":
        """No restrictions — auto-approve everything."""
        return cls(auto_approve=True)

    def blocks(self, tool_name: str) -> bool:
        lowered = tool_name.lower()
        if lowered in self.deny_names:
            return True
        return any(lowered.startswith(p) for p in self.deny_prefixes)

    def check_command_safety(self, command: str) -> str | None:
        """Returns a warning string if the command looks dangerous, else None."""
        cmd_lower = command.lower().strip()
        for pattern in DANGEROUS_PATTERNS:
            if pattern in cmd_lower:
                return f"Potentially dangerous: '{pattern}' detected in command"
        return None

    def request_permission(
        self,
        tool_name: str,
        description: str,
        confirm_fn: Callable[[], bool] | None = None,
    ) -> bool:
        """Check if a tool call should proceed. Returns True if approved."""
        if self.auto_approve:
            self.approvals.append(f"{tool_name}: {description}")
            return True

        if tool_name in ALWAYS_ALLOWED:
            return True

        if self.blocks(tool_name):
            self.denials.append({"tool": tool_name, "reason": "blocked by policy"})
            return False

        # For gated tools, ask for confirmation if a confirm_fn is provided
        if tool_name in GATED_TOOLS and confirm_fn:
            approved = confirm_fn()
            if not approved:
                self.denials.append({"tool": tool_name, "reason": "user denied"})
            return approved

        return True

    def summary(self) -> str:
        lines = [f"Permissions: {len(self.approvals)} approved, {len(self.denials)} denied"]
        for d in self.denials[-5:]:
            lines.append(f"  Denied: {d['tool']} — {d['reason']}")
        return "\n".join(lines)
