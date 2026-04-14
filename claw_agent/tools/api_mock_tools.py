"""API mock tools — spin up lightweight HTTP mock endpoints for testing."""

from __future__ import annotations

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict

# In-memory mock registry and running servers
_MOCKS: Dict[str, dict] = {}   # path → {status, headers, body}
_SERVERS: Dict[int, HTTPServer] = {}  # port → server


class _MockHandler(BaseHTTPRequestHandler):
    """Handler that returns mocked responses based on registered endpoints."""

    def _handle(self):
        path = self.path.split("?")[0]
        mock = _MOCKS.get(path)

        if mock:
            status = mock.get("status", 200)
            headers = mock.get("headers", {})
            body = mock.get("body", "")
        else:
            status = 404
            headers = {"Content-Type": "application/json"}
            body = json.dumps({"error": "not mocked", "path": path})

        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()

        if isinstance(body, str):
            body = body.encode("utf-8")
        self.wfile.write(body)

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PUT(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def do_PATCH(self):
        self._handle()

    def log_message(self, format, *args):
        pass  # Silence request logs


def mock_endpoint(path: str, status: int = 200, body: str = "", content_type: str = "application/json") -> str:
    """Register a mock response for a URL path.

    Parameters
    ----------
    path : str
        URL path to mock (e.g. ``/api/users``).
    status : int
        HTTP status code to return (default 200).
    body : str
        Response body to return.
    content_type : str
        Content-Type header value.
    """
    if not path.startswith("/"):
        path = "/" + path

    _MOCKS[path] = {
        "status": int(status),
        "headers": {"Content-Type": content_type},
        "body": body,
    }
    return f"Mock registered: {path} → {status}  ({len(body)} byte body)"


def mock_server(port: int = 9876) -> str:
    """Start a mock HTTP server on the given port.

    Register endpoints with ``mock_endpoint`` first, then start the server.
    """
    port = int(port)

    if port in _SERVERS:
        return f"Mock server already running on port {port}."

    if not _MOCKS:
        return "No mock endpoints registered. Use mock_endpoint first."

    try:
        server = HTTPServer(("127.0.0.1", port), _MockHandler)
    except OSError as exc:
        return f"Cannot start server on port {port}: {exc}"

    _SERVERS[port] = server

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    # brief pause to confirm startup
    time.sleep(0.2)

    endpoint_list = "\n".join(
        f"  {p} → {m['status']}" for p, m in _MOCKS.items()
    )
    return (
        f"Mock server started on http://127.0.0.1:{port}\n"
        f"Active endpoints:\n{endpoint_list}\n"
        f"Use stop_mock({port}) to shut down."
    )


def stop_mock(port: int = 9876) -> str:
    """Stop a running mock server.

    Parameters
    ----------
    port : int
        Port of the mock server to stop.
    """
    port = int(port)
    server = _SERVERS.pop(port, None)

    if server is None:
        return f"No mock server running on port {port}."

    server.shutdown()
    return f"Mock server on port {port} stopped. {len(_MOCKS)} endpoint definitions retained."
