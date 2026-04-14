"""MCP (Model Context Protocol) Server Support for Claw AI.

MCP allows Claw to connect to external tools and services via standardized protocol.
Supports: stdio, SSE, and HTTP transports.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
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
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
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


# ---- MCP Client Connection (JSON-RPC 2.0 over stdio) -----------------------

MCP_TOOL_CACHE = MCP_CONFIG_DIR / "tool_cache.json"


class MCPClientConnection:
    """Low-level JSON-RPC 2.0 connection to an MCP server over stdio."""

    def __init__(self, server: MCPServer):
        self.server = server
        self._process: subprocess.Popen | None = None
        self._req_id = 0
        self._started = False

    def connect(self) -> bool:
        """Start the server process and complete the MCP initialize handshake."""
        if self._started:
            return True
        try:
            env = {**os.environ, **self.server.env}
            self._process = subprocess.Popen(
                [self.server.command] + self.server.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,
            )
            resp = self._request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "claw-agent", "version": "0.1.0"},
            })
            if resp is None or "error" in (resp or {}):
                self.disconnect()
                return False
            self._notify("notifications/initialized")
            self._started = True
            return True
        except (OSError, FileNotFoundError):
            self._process = None
            return False

    def disconnect(self):
        """Terminate the server process."""
        if self._process:
            try:
                if self._process.stdin:
                    self._process.stdin.close()
            except Exception:
                pass
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None
        self._started = False

    # ---- JSON-RPC plumbing ---------------------------------------------------

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _read_line(self, timeout: float = 30) -> str | None:
        """Read one line from stdout with a timeout (cross-platform)."""
        result: list[str | None] = [None]
        proc = self._process

        def _reader():
            try:
                if proc and proc.stdout:
                    result[0] = proc.stdout.readline()
            except Exception:
                pass

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        t.join(timeout)
        return result[0]

    def _request(self, method: str, params: dict | None = None) -> dict | None:
        """Send a JSON-RPC request and wait for the matching response."""
        if not self._process or self._process.poll() is not None:
            return None
        req_id = self._next_id()
        msg: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            msg["params"] = params
        try:
            if not self._process.stdin:
                return None
            self._process.stdin.write(json.dumps(msg) + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, OSError):
            return None
        # Read until we get the response with our id (skip notifications)
        deadline = time.time() + 30
        while time.time() < deadline:
            line = self._read_line(max(1, deadline - time.time()))
            if not line:
                return None
            try:
                resp = json.loads(line.strip())
                if resp.get("id") == req_id:
                    return resp
            except json.JSONDecodeError:
                continue
        return None

    def _notify(self, method: str, params: dict | None = None):
        """Send a JSON-RPC notification (no response expected)."""
        if not self._process or self._process.poll() is not None:
            return
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        try:
            if not self._process.stdin:
                return
            self._process.stdin.write(json.dumps(msg) + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    # ---- MCP operations ------------------------------------------------------

    def list_tools(self) -> list[dict]:
        """Query the server for available tools."""
        if not self._started and not self.connect():
            return []
        resp = self._request("tools/list")
        if resp and "result" in resp:
            return resp["result"].get("tools", [])
        return []

    def call_tool(self, name: str, arguments: dict) -> str:
        """Invoke a tool on this server."""
        if not self._started and not self.connect():
            return f"Error: cannot connect to MCP server '{self.server.name}'"
        resp = self._request("tools/call", {"name": name, "arguments": arguments})
        if resp and "result" in resp:
            content = resp["result"].get("content", [])
            texts = [c.get("text", "") for c in content if c.get("type") == "text"]
            return "\n".join(texts) if texts else json.dumps(resp["result"])
        if resp and "error" in resp:
            err = resp["error"]
            return f"MCP error ({err.get('code', '?')}): {err.get('message', 'unknown')}"
        return f"Error: no response from MCP server '{self.server.name}'"


# ---- MCP Manager (tool discovery + routing) ---------------------------------

class MCPManager:
    """Discovers MCP tools and routes calls to the correct server."""

    def __init__(self):
        self._connections: dict[str, MCPClientConnection] = {}
        self._tool_map: dict[str, str] = {}        # namespaced_name -> server_name
        self._tool_defs: list[dict] = []           # OpenAI-format definitions
        self._original_names: dict[str, str] = {}  # namespaced_name -> original_name

    # ---- Discovery -----------------------------------------------------------

    def discover(self) -> None:
        """Connect to all enabled servers and discover their tools."""
        servers = load_mcp_config()
        if not servers:
            return
        self._tool_map.clear()
        self._tool_defs.clear()
        self._original_names.clear()

        for srv_name, server in servers.items():
            if not server.enabled:
                continue
            conn = MCPClientConnection(server)
            if not conn.connect():
                continue
            try:
                for tool in conn.list_tools():
                    ns_name = f"mcp_{srv_name}_{tool['name']}"
                    self._tool_map[ns_name] = srv_name
                    self._original_names[ns_name] = tool["name"]
                    self._tool_defs.append({
                        "type": "function",
                        "function": {
                            "name": ns_name,
                            "description": tool.get("description", f"MCP tool from {srv_name}"),
                            "parameters": tool.get("inputSchema", {
                                "type": "object", "properties": {},
                            }),
                        },
                    })
                self._connections[srv_name] = conn
            except Exception:
                conn.disconnect()

        self._save_cache()

    def load_from_cache(self) -> bool:
        """Load tool map from disk cache (no server connections needed)."""
        if not MCP_TOOL_CACHE.exists():
            return False
        try:
            with open(MCP_TOOL_CACHE, "r") as f:
                cache = json.load(f)
            self._tool_map = cache.get("tool_map", {})
            self._tool_defs = cache.get("tool_defs", [])
            self._original_names = cache.get("original_names", {})
            return bool(self._tool_map)
        except (json.JSONDecodeError, OSError, KeyError):
            return False

    def _save_cache(self):
        try:
            with open(MCP_TOOL_CACHE, "w") as f:
                json.dump({
                    "tool_map": self._tool_map,
                    "tool_defs": self._tool_defs,
                    "original_names": self._original_names,
                }, f, indent=2)
        except OSError:
            pass

    # ---- Execution -----------------------------------------------------------

    def has_tool(self, name: str) -> bool:
        return name in self._tool_map

    def get_tool_definitions(self) -> list[dict]:
        return list(self._tool_defs)

    def get_tool_names(self) -> set[str]:
        return set(self._tool_map.keys())

    def call_tool(self, name: str, arguments: dict) -> str:
        """Execute an MCP tool, starting the server connection if needed."""
        srv_name = self._tool_map.get(name)
        if not srv_name:
            return f"Error: MCP tool '{name}' not found"

        conn = self._connections.get(srv_name)
        if conn is None:
            servers = load_mcp_config()
            server = servers.get(srv_name)
            if not server:
                return f"Error: MCP server '{srv_name}' not configured"
            conn = MCPClientConnection(server)
            self._connections[srv_name] = conn

        original = self._original_names.get(name, name)
        return conn.call_tool(original, arguments)

    def shutdown(self):
        """Terminate all running MCP server connections."""
        for conn in self._connections.values():
            conn.disconnect()
        self._connections.clear()

    def get_context(self) -> str:
        """Enhanced context string listing actual MCP tool names."""
        if not self._tool_map:
            return get_mcp_context()
        servers = load_mcp_config()
        parts = ["\n## MCP Servers & Tools"]
        for srv_name, server in servers.items():
            if not server.enabled:
                continue
            tools = [t for t, s in self._tool_map.items() if s == srv_name]
            if tools:
                parts.append(f"- **{srv_name}** ({server.transport}): {len(tools)} tools")
                for t in tools:
                    for td in self._tool_defs:
                        if td["function"]["name"] == t:
                            desc = td["function"].get("description", "")[:80]
                            parts.append(f"  - {t}: {desc}")
                            break
            else:
                parts.append(f"- **{srv_name}** ({server.transport}): no tools discovered")
        return "\n".join(parts)


# ---- Standalone tool functions for MCP resource access ---------------------

def read_mcp_resource(server_name: str, resource_uri: str) -> str:
    """Read a resource from an MCP server.
    
    MCP servers can expose resources (files, database records, etc.) via URIs.
    Use list_mcp_resources first to discover available resource URIs.
    
    server_name: name of the configured MCP server
    resource_uri: URI of the resource (e.g. 'file:///path/to/doc.md')
    """
    servers = load_mcp_config()
    server = servers.get(server_name)
    if not server:
        configured = list(servers.keys()) or ["(none)"]
        return f"Error: MCP server '{server_name}' not found. Configured servers: {', '.join(configured)}"
    conn = MCPClientConnection(server)
    if not conn.connect():
        return f"Error: could not connect to MCP server '{server_name}'"
    try:
        resp = conn._request("resources/read", {"uri": resource_uri})
        if resp and "result" in resp:
            contents = resp["result"].get("contents", [])
            parts = []
            for c in contents:
                if c.get("type") == "text" or "text" in c:
                    parts.append(c.get("text", ""))
                elif c.get("type") == "blob":
                    parts.append(f"[binary blob: {c.get('mimeType', 'unknown')} {len(c.get('blob', ''))} bytes]")
            return "\n".join(parts) if parts else "(empty resource)"
        if resp and "error" in resp:
            err = resp["error"]
            return f"MCP error ({err.get('code', '?')}): {err.get('message', 'unknown')}"
        return "(no response from server)"
    except Exception as exc:
        return f"Error reading MCP resource: {exc}"
    finally:
        conn.disconnect()


def list_mcp_resources(server_name: str) -> str:
    """List available resources from an MCP server.
    
    Returns the URI and description of each resource exposed by the server.
    """
    servers = load_mcp_config()
    server = servers.get(server_name)
    if not server:
        configured = list(servers.keys()) or ["(none)"]
        return f"Error: MCP server '{server_name}' not found. Configured servers: {', '.join(configured)}"
    conn = MCPClientConnection(server)
    if not conn.connect():
        return f"Error: could not connect to MCP server '{server_name}'"
    try:
        resp = conn._request("resources/list", {})
        if resp and "result" in resp:
            resources = resp["result"].get("resources", [])
            if not resources:
                return f"No resources available from '{server_name}'"
            lines = [f"Resources from '{server_name}' ({len(resources)}):"]
            for r in resources:
                uri = r.get("uri", "?")
                name = r.get("name", "")
                desc = r.get("description", "")
                lines.append(f"  {uri}" + (f" — {name}" if name else "") + (f": {desc}" if desc else ""))
            return "\n".join(lines)
        return f"No resources response from '{server_name}'"
    except Exception as exc:
        return f"Error listing MCP resources: {exc}"
    finally:
        conn.disconnect()

