#!/usr/bin/env python3
"""MCP Server providing ChatGPT access via g4f (GPT4Free).

Exposes a chat_completion tool over JSON-RPC 2.0 stdio transport.
Spawned by claw-agent's MCPClientConnection as a subprocess.

Requires: pip install g4f
"""

from __future__ import annotations

import json
import sys
import time

# g4f must be installed
try:
    from g4f.client import Client as G4FClient
    _USE_NEW_API = True
except ImportError:
    try:
        import g4f
        _USE_NEW_API = False
    except ImportError:
        print(json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32000, "message": "g4f not installed. Run: pip install g4f"},
        }))
        sys.exit(1)


SERVER_INFO = {
    "name": "chatgpt-g4f",
    "version": "0.1.0",
}

SUPPORTED_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
]

TOOL_DEFINITION = {
    "name": "chat_completion",
    "description": "Query a ChatGPT model via g4f (free, no API key needed)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": f"Model to use. Supported: {', '.join(SUPPORTED_MODELS)}",
                "enum": SUPPORTED_MODELS,
            },
            "prompt": {
                "type": "string",
                "description": "The user message/prompt",
            },
            "system_prompt": {
                "type": "string",
                "description": "Optional system prompt",
                "default": "",
            },
        },
        "required": ["model", "prompt"],
    },
}


def query_g4f(model: str, prompt: str, system_prompt: str = "") -> str:
    """Query a model using g4f."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    if _USE_NEW_API:
        client = G4FClient()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content or ""
    else:
        response = g4f.ChatCompletion.create(
            model=model,
            messages=messages,
        )
        return response if isinstance(response, str) else str(response)


def handle_request(request: dict) -> dict | None:
    """Handle a JSON-RPC 2.0 request."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }

    if method == "notifications/initialized":
        return None  # Notification, no response

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": [TOOL_DEFINITION]},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name != "chat_completion":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"},
            }

        model = arguments.get("model", "gpt-4o-mini")
        prompt = arguments.get("prompt", "")
        system_prompt = arguments.get("system_prompt", "")

        if model not in SUPPORTED_MODELS:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error: unsupported model '{model}'"}],
                    "isError": True,
                },
            }

        try:
            result = query_g4f(model, prompt, system_prompt)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": result}],
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"g4f error: {e}"}],
                    "isError": True,
                },
            }

    # Unknown method
    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    return None


def main():
    """Main loop: read JSON-RPC from stdin, write to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
