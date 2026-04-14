"""Validation tools — JSON schema, YAML lint, URL checking."""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from pathlib import Path


def validate_json_schema(data_path: str, schema_path: str) -> str:
    """Validate a JSON file against a JSON Schema.

    Uses a lightweight built-in checker (no jsonschema dependency).
    Checks required fields, types, and enum constraints.
    """
    dp = Path(data_path).expanduser().resolve()
    sp = Path(schema_path).expanduser().resolve()

    if not dp.exists():
        return f"Data file not found: {data_path}"
    if not sp.exists():
        return f"Schema file not found: {schema_path}"

    try:
        data = json.loads(dp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"Invalid JSON in data file: {exc}"

    try:
        schema = json.loads(sp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"Invalid JSON in schema file: {exc}"

    errors = _check_schema(data, schema, path="$")
    if not errors:
        return f"VALID — {dp.name} passes the schema."
    return f"INVALID — {len(errors)} error(s):\n" + "\n".join(f"  • {e}" for e in errors[:20])


def _check_schema(data, schema: dict, path: str) -> list[str]:
    """Lightweight recursive schema checker."""
    errors: list[str] = []
    expected_type = schema.get("type")

    TYPE_MAP = {
        "string": str, "number": (int, float), "integer": int,
        "boolean": bool, "array": list, "object": dict, "null": type(None),
    }

    if expected_type and expected_type in TYPE_MAP:
        if not isinstance(data, TYPE_MAP[expected_type]):
            errors.append(f"{path}: expected {expected_type}, got {type(data).__name__}")
            return errors

    if expected_type == "object":
        props = schema.get("properties", {})
        required = schema.get("required", [])
        if isinstance(data, dict):
            for req in required:
                if req not in data:
                    errors.append(f"{path}: missing required property '{req}'")
            for key, sub_schema in props.items():
                if key in data:
                    errors.extend(_check_schema(data[key], sub_schema, f"{path}.{key}"))

    if expected_type == "array" and isinstance(data, list):
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(data[:50]):
                errors.extend(_check_schema(item, items_schema, f"{path}[{i}]"))

    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{path}: value {data!r} not in enum {schema['enum']}")

    return errors


def validate_yaml(filepath: str) -> str:
    """Check a YAML file for syntax errors.

    Uses a basic structural check if PyYAML is not installed.
    """
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        return f"File not found: {filepath}"

    text = path.read_text(encoding="utf-8")

    # Try PyYAML first
    try:
        import yaml
        try:
            docs = list(yaml.safe_load_all(text))
            return f"VALID YAML — {len(docs)} document(s) in {path.name}"
        except yaml.YAMLError as exc:
            return f"INVALID YAML in {path.name}:\n{exc}"
    except ImportError:
        pass

    # Fallback: basic checks
    issues: list[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        if "\t" in line:
            issues.append(f"  Line {i}: tabs found (YAML requires spaces)")
        if line.rstrip() != line and line.strip():
            pass  # trailing whitespace is technically allowed
        # Check for obvious structural issues
        if re.match(r"^\s+\S", line) and not re.match(r"^\s+-\s|^\s+\w+\s*:", line):
            if not line.strip().startswith("#") and not line.strip().startswith("-"):
                issues.append(f"  Line {i}: suspicious indentation")

    if issues:
        return f"Potential YAML issues in {path.name}:\n" + "\n".join(issues[:20])
    return f"Basic YAML check passed for {path.name} (install PyYAML for full validation)"


def check_url(url: str, timeout: int = 10) -> str:
    """Check if a URL is reachable and report status code + headers."""
    if not re.match(r"https?://", url):
        return f"Invalid URL (must start with http:// or https://): {url}"

    timeout = max(1, min(int(timeout), 30))

    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "ClawAI-URLCheck/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            ct = resp.headers.get("Content-Type", "unknown")
            cl = resp.headers.get("Content-Length", "unknown")
            server = resp.headers.get("Server", "unknown")
            return (
                f"URL: {url}\n"
                f"Status: {status}\n"
                f"Content-Type: {ct}\n"
                f"Content-Length: {cl}\n"
                f"Server: {server}"
            )
    except urllib.error.HTTPError as exc:
        return f"URL: {url}\nHTTP Error: {exc.code} {exc.reason}"
    except urllib.error.URLError as exc:
        return f"URL: {url}\nConnection Error: {exc.reason}"
    except Exception as exc:
        return f"URL: {url}\nError: {exc}"
