"""Bridge between VS Code extension and Claw Agent.

Reads JSON messages from stdin, runs agent with streaming, emits JSON events to stdout.
This is spawned by the VS Code extension as a child process.
"""

from __future__ import annotations

import argparse
import json
import sys
import os

# claw_agent is pip-installed (editable). If not on path, add the project root.
try:
    import claw_agent  # noqa: F401
except ImportError:
    # Fallback: try project root relative to this file
    _root = os.path.join(os.path.dirname(__file__), "..", "..")
    if os.path.isdir(os.path.join(_root, "claw_agent")):
        sys.path.insert(0, _root)
    # Also try the main project location
    _project = os.path.expanduser(r"~\Pictures\ClaudeAI\claw-agent")
    if os.path.isdir(os.path.join(_project, "claw_agent")):
        sys.path.insert(0, _project)

from claw_agent.agent import (
    Agent, TextDelta, ToolCallStart, ToolCallEnd, TurnComplete, AgentDone,
)
from claw_agent.permissions import PermissionContext
from claw_agent.sessions import Session


def emit(event: dict):
    """Send a JSON event to stdout for the VS Code extension."""
    sys.stdout.write(json.dumps(event) + "\n")
    sys.stdout.flush()


def format_args(args: dict) -> str:
    parts = []
    for k, v in args.items():
        sv = str(v)
        if len(sv) > 50:
            sv = sv[:47] + "..."
        parts.append(f"{k}={sv}")
    return ", ".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="deepseek-r1:671b")
    parser.add_argument("--base-url", default="http://localhost:11434")
    args = parser.parse_args()

    def create_agent():
        return Agent(
            model=args.model,
            base_url=args.base_url,
            permissions=PermissionContext.default(),
            session=Session(model=args.model),
        )

    agent = create_agent()
    emit({"type": "status", "text": f"Ready — {args.model}"})

    # Read JSON messages from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            emit({"type": "error", "text": "Invalid JSON"})
            continue

        if msg.get("type") == "chat" or (not msg.get("type") and msg.get("text")):
            content = msg.get("content") or msg.get("text", "")
            if not content:
                continue

            try:
                tool_count = 0
                MAX_TOOLS_PER_MSG = 15  # hard cap per user message
                final_text = ""

                for event in agent.stream_chat(content):
                    if isinstance(event, TextDelta):
                        emit({"type": "text_delta", "text": event.text})

                    elif isinstance(event, ToolCallStart):
                        tool_count += 1
                        if tool_count > MAX_TOOLS_PER_MSG:
                            emit({"type": "error", "text": f"Tool call limit ({MAX_TOOLS_PER_MSG}) reached — stopping."})
                            break
                        emit({
                            "type": "tool_start",
                            "name": event.name,
                            "args": format_args(event.arguments),
                        })

                    elif isinstance(event, ToolCallEnd):
                        result_preview = event.result[:300] if event.result else ""
                        emit({
                            "type": "tool_end",
                            "name": event.name,
                            "result": result_preview,
                            "duration_ms": event.duration_ms,
                        })

                    elif isinstance(event, AgentDone):
                        final_text = event.final_text

                # The repo-local bridge tests read until cost, so emit done first
                # here and let the cost summary follow immediately after.
                emit({"type": "done", "text": final_text})
                summary = agent.cost.summary()
                emit({"type": "cost", "text": str(summary)})

            except Exception as e:
                emit({"type": "error", "text": f"Error: {e}"})
                emit({"type": "done", "text": ""})
                # Recreate agent with fresh state on crash
                try:
                    agent = create_agent()
                    emit({"type": "status", "text": f"Recovered — {args.model}"})
                except Exception as re_err:
                    emit({"type": "error", "text": f"Recovery failed: {re_err}"})


if __name__ == "__main__":
    main()
