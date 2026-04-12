"""MCP (Model Context Protocol) Server Support for Claw AI.

MCP allows Claw to connect to external tools and services via standardized protocol.
Supports: stdio, SSE, and HTTP transports.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

# MCP configuration directory
MCP_CONFIG_DIR = Path.home() / ".claw-agent" / "mcp"
MCP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
MCP_CONFIG_FILE = MCP_CONFIG_DIR / "config.json"


@dataclass
class MCPServer:
    """MCP Server configuration."""
    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    transport: str  # "stdio", "sse", "http"
    enabled: bool = True


def load_mcp_config() -> dict[str, MCPServer]:
    """Load MCP server configurations."""
    if not MCP_CONFIG_FILE.exists():
        return {}
    
    with open(MCP_CONFIG_FILE, "r") as f:
        data = json.load(f)
    
    servers = {}
    for name, config in data.get("mcpServers", {}).items():
        servers[name] = MCPServer(
            name=name,
            command=config.get("command", ""),
            args=config.get("args", []),
            env=config.get("env", {}),
            transport=config.get("transport", "stdio"),
            enabled=config.get("enabled", True),
        )
    
    return servers


def save_mcp_config(servers: dict[str, MCPServer]):
    """Save MCP server configurations."""
    data = {
        "mcpServers": {
            name: {
                "command": server.command,
                "args": server.args,
                "env": server.env,
                "transport": server.transport,
                "enabled": server.enabled,
            }
            for name, server in servers.items()
        }
    }
    
    with open(MCP_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_mcp_server(
    name: str,
    command: str,
    args: list[str] = None,
    env: dict[str, str] = None,
    transport: str = "stdio",
) -> str:
    """Add an MCP server configuration."""
    servers = load_mcp_config()
    
    if name in servers:
        return f"✗ MCP server '{name}' already exists"
    
    servers[name] = MCPServer(
        name=name,
        command=command,
        args=args or [],
        env=env or {},
        transport=transport,
        enabled=True,
    )
    
    save_mcp_config(servers)
    return f"✓ Added MCP server: {name}"


def remove_mcp_server(name: str) -> str:
    """Remove an MCP server configuration."""
    servers = load_mcp_config()
    
    if name not in servers:
        return f"✗ MCP server '{name}' not found"
    
    del servers[name]
    save_mcp_config(servers)
    return f"✓ Removed MCP server: {name}"


def list_mcp_servers() -> list[dict[str, Any]]:
    """List all configured MCP servers."""
    servers = load_mcp_config()
    return [
        {
            "name": s.name,
            "command": s.command,
            "args": s.args,
            "transport": s.transport,
            "enabled": s.enabled,
        }
        for s in servers.values()
    ]


def get_mcp_context() -> str:
    """Get context string about active MCP servers."""
    servers = load_mcp_config()
    if not servers:
        return ""
    
    context = "\n## MCP Servers\n"
    for name, server in servers.items():
        if server.enabled:
            context += f"- {name}: {server.command} ({server.transport})\n"
    
    return context
