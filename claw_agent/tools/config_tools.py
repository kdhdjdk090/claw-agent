"""Config tools — read/write JSON, YAML, TOML, INI config files + JSON schema validation."""

from __future__ import annotations

import configparser
import json
import os
from pathlib import Path


def read_config(file_path: str) -> str:
    """Read a config file (JSON, YAML, TOML, or INI) and pretty-print its contents."""
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    ext = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"Error reading file: {exc}"

    # JSON
    if ext in (".json", ".jsonc"):
        try:
            # Strip comments for .jsonc
            clean = text
            if ext == ".jsonc":
                import re
                clean = re.sub(r"//.*$", "", text, flags=re.MULTILINE)
                clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL)
            data = json.loads(clean)
            return f"Config ({path.name}):\n{json.dumps(data, indent=2, ensure_ascii=False)}"
        except json.JSONDecodeError as exc:
            return f"JSON parse error: {exc}"

    # YAML
    if ext in (".yaml", ".yml"):
        try:
            import yaml
            data = yaml.safe_load(text)
            return f"Config ({path.name}):\n{json.dumps(data, indent=2, ensure_ascii=False, default=str)}"
        except ImportError:
            return f"Config ({path.name}) [raw YAML — install PyYAML for parsed view]:\n{text[:5000]}"
        except Exception as exc:
            return f"YAML parse error: {exc}"

    # TOML
    if ext == ".toml":
        # Python 3.11+ has tomllib
        try:
            import tomllib
            data = tomllib.loads(text)
            return f"Config ({path.name}):\n{json.dumps(data, indent=2, ensure_ascii=False, default=str)}"
        except ImportError:
            try:
                import tomli
                data = tomli.loads(text)
                return f"Config ({path.name}):\n{json.dumps(data, indent=2, ensure_ascii=False, default=str)}"
            except ImportError:
                return f"Config ({path.name}) [raw TOML — Python 3.11+ or pip install tomli]:\n{text[:5000]}"
        except Exception as exc:
            return f"TOML parse error: {exc}"

    # INI / .cfg / .conf
    if ext in (".ini", ".cfg", ".conf", ".properties"):
        try:
            cp = configparser.ConfigParser()
            cp.read_string(text)
            result = {}
            for section in cp.sections():
                result[section] = dict(cp[section])
            if cp.defaults():
                result["DEFAULT"] = dict(cp.defaults())
            return f"Config ({path.name}):\n{json.dumps(result, indent=2, ensure_ascii=False)}"
        except Exception as exc:
            return f"INI parse error: {exc}"

    # .env files
    if path.name.startswith(".env") or ext == ".env":
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(stripped)
        return f"Config ({path.name}):\n" + "\n".join(lines)

    return f"Config ({path.name}) [unknown format]:\n{text[:5000]}"


def write_config(file_path: str, key: str, value: str) -> str:
    """Set a key in a JSON config file. Creates the file if it doesn't exist.

    Args:
        file_path: Path to JSON config file.
        key: Dot-notation key path (e.g. 'server.port').
        value: Value to set (auto-detects int, float, bool, null, or string).
    """
    path = Path(file_path).expanduser().resolve()

    # Load existing or start fresh
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return f"Error: Cannot parse existing file as JSON — {file_path}"

    # Parse value type
    parsed_value: object = value
    if value.lower() == "true":
        parsed_value = True
    elif value.lower() == "false":
        parsed_value = False
    elif value.lower() == "null" or value.lower() == "none":
        parsed_value = None
    else:
        try:
            parsed_value = int(value)
        except ValueError:
            try:
                parsed_value = float(value)
            except ValueError:
                # Try JSON array/object
                try:
                    parsed_value = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    parsed_value = value  # Keep as string

    # Navigate + set
    parts = key.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current or not isinstance(current.get(part), dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = parsed_value

    # Write
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return f"Set {key} = {json.dumps(parsed_value)} in {path.name}"


def validate_json(text_or_file: str, schema: str = "") -> str:
    """Validate JSON syntax and optionally against a JSON Schema.

    Args:
        text_or_file: JSON string or path to a JSON file.
        schema: Optional JSON Schema string or file path.
    """
    # Load target JSON
    path = Path(text_or_file).expanduser().resolve()
    if path.exists() and path.is_file():
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
            source = path.name
        except json.JSONDecodeError as exc:
            return f"Invalid JSON in {path.name}: {exc}"
    else:
        try:
            data = json.loads(text_or_file)
            source = "input"
        except json.JSONDecodeError as exc:
            return f"Invalid JSON: {exc}"

    if not schema:
        return f"Valid JSON ({source}): {type(data).__name__} with {len(data) if hasattr(data, '__len__') else '?'} items"

    # Load schema
    schema_path = Path(schema).expanduser().resolve()
    if schema_path.exists():
        try:
            schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return f"Error loading schema file: {exc}"
    else:
        try:
            schema_data = json.loads(schema)
        except Exception as exc:
            return f"Error parsing schema: {exc}"

    try:
        import jsonschema
        jsonschema.validate(data, schema_data)
        return f"Valid: JSON ({source}) passes schema validation"
    except ImportError:
        return f"Valid JSON syntax. Install jsonschema for schema validation: pip install jsonschema"
    except Exception as exc:
        return f"Schema validation failed: {exc}"
