"""HTTP client tools — full REST support (GET/POST/PUT/DELETE/PATCH)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str = "",
    content_type: str = "application/json",
    timeout: int = 30,
) -> str:
    """Send an HTTP request and return status + body.

    Args:
        url: Full URL (must start with http:// or https://).
        method: HTTP method — GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS.
        headers: Optional dict of extra headers.
        body: Request body (for POST/PUT/PATCH). String or JSON string.
        content_type: Content-Type header value.
        timeout: Seconds before timeout.
    """
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    method = method.upper()
    if method not in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
        return f"Error: unsupported method '{method}'"

    all_headers = {"User-Agent": "ClawAI/1.0"}
    if body and method in ("POST", "PUT", "PATCH"):
        all_headers["Content-Type"] = content_type
    if headers:
        all_headers.update(headers)

    data = body.encode("utf-8") if body else None

    req = urllib.request.Request(url, data=data, headers=all_headers, method=method)

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - start
            resp_body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
            resp_headers = dict(resp.getheaders())
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        resp_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        status = e.code
        resp_headers = dict(e.headers.items()) if e.headers else {}
    except urllib.error.URLError as e:
        return f"Error: {e.reason}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

    # Truncate large responses
    if len(resp_body) > 50_000:
        resp_body = resp_body[:50_000] + f"\n\n... [truncated, {len(resp_body)} bytes total]"

    lines = [
        f"HTTP {status} — {method} {url}",
        f"Time: {elapsed:.2f}s",
        f"Content-Type: {resp_headers.get('Content-Type', 'unknown')}",
        f"Content-Length: {resp_headers.get('Content-Length', 'unknown')}",
        "",
        resp_body,
    ]
    return "\n".join(lines)
