"""ChatGPT via MCP Bridge — access ChatGPT models through g4f MCP server.

Uses the g4f (GPT4Free) MCP server running as a subprocess.
No OpenAI API key required. Models are prefixed with 'chatgpt/' in the council.

Follows the same provider pattern as alibaba_cloud.py.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .mcp import MCPClientConnection, MCPServer
from .python_runtime import get_python_executable


# ChatGPT models available via g4f MCP server (council-facing names)
MCP_CHATGPT_MODELS = [
    "chatgpt/gpt-4o",
    "chatgpt/gpt-4o-mini",
    "chatgpt/gpt-4-turbo",
]

# Map council name → g4f model name
_MODEL_MAP = {
    "chatgpt/gpt-4o": "gpt-4o",
    "chatgpt/gpt-4o-mini": "gpt-4o-mini",
    "chatgpt/gpt-4-turbo": "gpt-4-turbo",
}

# Path to the MCP server script
_SERVER_SCRIPT = Path(__file__).parent / "mcp_servers" / "chatgpt_server.py"


@dataclass
class ChatGPTResponse:
    """Response from ChatGPT via MCP bridge."""
    model: str
    content: str
    token_count: int = 0
    latency_ms: float = 0
    error: str = ""


class ChatGPTMCPClient:
    """Client for ChatGPT access via the g4f MCP server.

    Manages a persistent connection to the MCP server subprocess.
    The server is spawned lazily on first query and reused across calls.
    """

    def __init__(self):
        self._conn: Optional[MCPClientConnection] = None
        self.total_calls = 0

    def _ensure_connection(self) -> MCPClientConnection:
        """Lazily start and connect to the MCP server."""
        if self._conn is not None and self._conn._started:
            return self._conn

        server = MCPServer(
            name="chatgpt-g4f",
            command=get_python_executable(),
            args=[str(_SERVER_SCRIPT)],
            env={},
            transport="stdio",
            enabled=True,
        )
        self._conn = MCPClientConnection(server)
        if not self._conn.connect():
            raise ConnectionError(
                "Failed to start ChatGPT MCP server. "
                "Is g4f installed? Run: pip install g4f"
            )
        return self._conn

    def close(self):
        """Disconnect from the MCP server."""
        if self._conn:
            self._conn.disconnect()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def query(self, model: str, prompt: str, system_prompt: str = "") -> ChatGPTResponse:
        """Query a ChatGPT model via the MCP bridge."""
        start = time.time()
        g4f_model = _MODEL_MAP.get(model, model.split("/")[-1])

        try:
            conn = self._ensure_connection()
            result_text = conn.call_tool("chat_completion", {
                "model": g4f_model,
                "prompt": prompt,
                "system_prompt": system_prompt,
            })

            latency_ms = (time.time() - start) * 1000
            self.total_calls += 1

            # Check for MCP-level or g4f errors
            if result_text.startswith(("Error:", "MCP error", "g4f error")):
                return ChatGPTResponse(
                    model=model,
                    content="",
                    latency_ms=latency_ms,
                    error=result_text,
                )

            return ChatGPTResponse(
                model=model,
                content=result_text,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return ChatGPTResponse(
                model=model,
                content="",
                latency_ms=latency_ms,
                error=str(e),
            )
