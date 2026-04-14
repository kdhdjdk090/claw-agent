"""Network tools — ping, DNS lookup, TCP port check."""

from __future__ import annotations

import platform
import re
import socket
import subprocess


def ping_host(host: str, count: int = 4) -> str:
    """Ping a hostname or IP address.

    Args:
        host: Hostname or IP to ping.
        count: Number of pings (default 4).
    """
    if not host or not host.strip():
        return "Error: No host specified"

    count = max(1, min(count, 20))
    system = platform.system().lower()

    try:
        if system == "windows":
            cmd = ["ping", "-n", str(count), host]
        else:
            cmd = ["ping", "-c", str(count), host]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=count * 5 + 10
        )
        output = result.stdout + result.stderr
        return f"Ping {host} (count={count}):\n\n{output.strip()}"
    except subprocess.TimeoutExpired:
        return f"Ping {host}: timed out after {count * 5 + 10}s"
    except FileNotFoundError:
        return "Error: ping command not found"
    except Exception as exc:
        return f"Error pinging {host}: {exc}"


def dns_lookup(hostname: str, record_type: str = "A") -> str:
    """Resolve a hostname to IP addresses.

    Args:
        hostname: Domain name to look up.
        record_type: Record type — A, AAAA, CNAME, MX, TXT, NS (default A).
    """
    if not hostname or not hostname.strip():
        return "Error: No hostname specified"

    record_type = record_type.upper()
    lines = [f"DNS Lookup: {hostname} ({record_type})"]

    # Basic A/AAAA resolution via socket
    if record_type in ("A", "AAAA"):
        try:
            family = socket.AF_INET if record_type == "A" else socket.AF_INET6
            results = socket.getaddrinfo(hostname, None, family, socket.SOCK_STREAM)
            seen = set()
            for af, socktype, proto, canonname, addr in results:
                ip = addr[0]
                if ip not in seen:
                    seen.add(ip)
                    lines.append(f"  {record_type}: {ip}")
            if not seen:
                lines.append("  No records found")
        except socket.gaierror as exc:
            lines.append(f"  Error: {exc}")
        return "\n".join(lines)

    # For MX, TXT, NS, CNAME — try nslookup CLI
    try:
        cmd = ["nslookup", f"-type={record_type}", hostname]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = (result.stdout + result.stderr).strip()
        lines.append(output)
    except FileNotFoundError:
        # Fallback to socket for basic resolution
        try:
            ip = socket.gethostbyname(hostname)
            lines.append(f"  A: {ip}")
            lines.append(f"  (nslookup not available; showing basic A record)")
        except socket.gaierror as exc:
            lines.append(f"  Error: {exc}")
    except Exception as exc:
        lines.append(f"  Error: {exc}")

    return "\n".join(lines)


def check_port(host: str, port: int, timeout: float = 5.0) -> str:
    """Check if a TCP port is open on a host.

    Args:
        host: Hostname or IP.
        port: TCP port number.
        timeout: Connection timeout in seconds (default 5).
    """
    if not host:
        return "Error: No host specified"
    if not (1 <= port <= 65535):
        return f"Error: Invalid port {port} (must be 1–65535)"

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            # Try to grab banner
            try:
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock2.settimeout(2)
                sock2.connect((host, port))
                sock2.send(b"\r\n")
                banner = sock2.recv(256).decode("utf-8", errors="replace").strip()
                sock2.close()
                return f"Port {port} on {host}: OPEN (banner: {banner[:100]})"
            except Exception:
                return f"Port {port} on {host}: OPEN"
        else:
            return f"Port {port} on {host}: CLOSED (error code {result})"
    except socket.timeout:
        return f"Port {port} on {host}: FILTERED (timeout after {timeout}s)"
    except socket.gaierror:
        return f"Error: Cannot resolve hostname {host}"
    except Exception as exc:
        return f"Error checking port: {exc}"
