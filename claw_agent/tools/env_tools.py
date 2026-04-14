"""Environment / .env file management tools."""

from __future__ import annotations

import os
from pathlib import Path


def read_env(filepath: str = ".env") -> str:
    """Read and display a .env file (masking secret values).

    Masks values for keys containing SECRET, KEY, TOKEN, PASSWORD, CREDENTIAL, AUTH.
    """
    fp = Path(filepath).expanduser().resolve()
    if not fp.is_file():
        return f"Error: .env file not found — {filepath}"

    SENSITIVE = {"secret", "key", "token", "password", "credential", "auth", "apikey", "api_key"}

    try:
        lines = fp.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        return f"Error reading file: {e}"

    output = [f"Environment file: {fp}\n"]
    count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            output.append(line)
            continue

        if "=" in stripped:
            key, _, val = stripped.partition("=")
            key = key.strip()
            val = val.strip().strip("'\"")
            is_sensitive = any(s in key.lower() for s in SENSITIVE)
            display_val = "****" if is_sensitive and val else val if not val else val
            if is_sensitive and val:
                display_val = val[:3] + "****" if len(val) > 3 else "****"
            output.append(f"{key}={display_val}")
            count += 1
        else:
            output.append(line)

    output.append(f"\n{count} variable(s) found.")
    return "\n".join(output)


def write_env(key: str, value: str, filepath: str = ".env") -> str:
    """Set or update a variable in a .env file.

    If the key exists, updates it. If not, appends it.
    Creates the file if it doesn't exist.
    """
    if not key or not key.strip():
        return "Error: key is required."

    key = key.strip()
    fp = Path(filepath).expanduser().resolve()

    lines = []
    if fp.is_file():
        try:
            lines = fp.read_text(encoding="utf-8").splitlines()
        except Exception as e:
            return f"Error reading file: {e}"

    # Check if key already exists
    found = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            existing_key = stripped.split("=", 1)[0].strip()
            if existing_key == key:
                new_lines.append(f"{key}={value}")
                found = True
                continue
        new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}")

    try:
        fp.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    except Exception as e:
        return f"Error writing file: {e}"

    action = "Updated" if found else "Added"
    return f"✅ {action} {key} in {fp}"


def set_env_var(key: str, value: str) -> str:
    """Set an environment variable in the current process.

    This only affects the current running process, not the system or shell.
    """
    if not key or not key.strip():
        return "Error: key is required."
    os.environ[key.strip()] = value
    return f"✅ Set environment variable: {key.strip()}"
