"""Validation utilities for Claw Agent.

Provides validation functions for API keys, file paths, URLs, and other inputs
to ensure security and correctness before operations are executed.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass


def validate_api_key(key: str | None, provider: str) -> str:
    """Validate that an API key is present and properly formatted.
    
    Args:
        key: The API key to validate
        provider: Name of the API provider (for error messages)
    
    Returns:
        The validated API key
    
    Raises:
        ConfigurationError: If the key is missing or invalid format
    """
    if not key:
        raise ConfigurationError(
            f"{provider} API key is not configured. "
            f"Set {provider.upper()}_API_KEY environment variable."
        )
    
    # Basic format validation - most API keys are at least 20 chars
    if len(key) < 20:
        raise ConfigurationError(
            f"{provider} API key appears to be too short ({len(key)} chars). "
            "Check your environment variable."
        )
    
    # Check for common placeholder patterns
    if key in ("your-api-key", "xxx", "REPLACE_ME", "TODO"):
        raise ConfigurationError(
            f"{provider} API key appears to be a placeholder. "
            "Please set a valid API key."
        )
    
    return key


def validate_file_path(path: str, workspace_root: str | Path | None = None, 
                       must_exist: bool = False) -> Path:
    """Validate and resolve a file path with security checks.
    
    Args:
        path: The file path to validate
        workspace_root: Optional root directory to constrain access
        must_exist: If True, verify the file/directory exists
    
    Returns:
        Resolved Path object
    
    Raises:
        SecurityError: If path traversal is detected
        FileNotFoundError: If must_exist=True and path doesn't exist
    """
    resolved = Path(path).expanduser().resolve()
    
    # Check for path traversal if workspace root is specified
    if workspace_root:
        workspace = Path(workspace_root).resolve()
        try:
            resolved.relative_to(workspace)
        except ValueError:
            raise SecurityError(
                f"Path traversal detected: {path} is outside workspace {workspace}"
            )
    
    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    
    return resolved


def validate_url(url: str, allowed_protocols: set[str] | None = None,
                 max_length: int = 2048) -> str:
    """Validate a URL for security and correctness.
    
    Args:
        url: The URL to validate
        allowed_protocols: Set of allowed protocols (default: http, https)
        max_length: Maximum allowed URL length
    
    Returns:
        The validated URL
    
    Raises:
        SecurityError: If URL is invalid or uses disallowed protocol
    """
    if not url:
        raise SecurityError("URL cannot be empty")
    
    if len(url) > max_length:
        raise SecurityError(f"URL exceeds maximum length ({len(url)} > {max_length})")
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise SecurityError(f"Invalid URL format: {e}")
    
    # Check protocol
    if allowed_protocols is None:
        allowed_protocols = {"http", "https"}
    
    if parsed.scheme.lower() not in allowed_protocols:
        raise SecurityError(
            f"Disallowed protocol '{parsed.scheme}'. Allowed: {allowed_protocols}"
        )
    
    # Basic domain validation
    if not parsed.netloc:
        raise SecurityError("URL must have a valid domain")
    
    return url


def validate_command(command: str, blocklist: set[str] | None = None) -> str:
    """Validate a shell command for security.
    
    Args:
        command: The command to validate
        blocklist: Set of dangerous patterns to block
    
    Returns:
        The validated command
    
    Raises:
        SecurityError: If command contains dangerous patterns
    """
    if not command:
        raise SecurityError("Command cannot be empty")
    
    if blocklist is None:
        blocklist = {
            "rm -rf /",
            "rm -rf /*",
            "dd if=/dev/zero",
            ":(){:|:&};:",
            "mkfs",
            "chmod -R 777 /",
            "chown -R",
            "> /dev/sda",
            "sudo rm",
            "sudo chmod",
            "sudo dd",
            "wget.*\\|.*sh",
            "curl.*\\|.*sh",
        }
    
    # Check for blocklisted patterns
    command_lower = command.lower()
    for pattern in blocklist:
        if pattern.lower() in command_lower:
            raise SecurityError(f"Command contains dangerous pattern: {pattern}")
    
    # Check for obvious injection attempts
    injection_patterns = [
        r"\$\(",  # Command substitution
        r"`.*`",  # Backtick execution
        r";\s*rm\s",  # Chained rm
        r"\|\s*.*\s*>\s*/dev/",  # Pipe to /dev/
        r">\s*/dev/sd",  # Write to disk device
        r"mkfs\.",  # Format filesystem
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, command):
            raise SecurityError(f"Command contains potential injection: {pattern}")
    
    return command


def validate_import_module(module_name: str, allowlist: set[str] | None = None) -> str:
    """Validate a module name for safe importing.
    
    Args:
        module_name: The module name to validate
        allowlist: Set of allowed module names
    
    Returns:
        The validated module name
    
    Raises:
        SecurityError: If module is not in allowlist
    """
    if not module_name:
        raise SecurityError("Module name cannot be empty")
    
    if allowlist is None:
        # Default allowlist for PDF modules
        allowlist = {"pypdf", "PyPDF2", "pdfminer", "pdfminer.six"}
    
    # Check exact match first
    if module_name in allowlist:
        return module_name
    
    # Check if it's a submodule of an allowed package
    for allowed in allowlist:
        if module_name.startswith(allowed + "."):
            return module_name
    
    raise SecurityError(
        f"Module '{module_name}' is not in the allowed list: {allowlist}"
    )


def validate_environment_config() -> dict[str, Any]:
    """Validate all required environment configuration.
    
    Returns:
        Dictionary of validated configuration
        
    Raises:
        ConfigurationError: If required configuration is missing
    """
    config = {}
    errors = []
    
    # Check API keys (optional but warn if missing)
    api_keys = {
        "OPENROUTER": os.environ.get("OPENROUTER_API_KEY", ""),
        "DASHSCOPE": os.environ.get("DASHSCOPE_API_KEY", ""),
        "DEEPSEEK": os.environ.get("DEEPSEEK_API_KEY", ""),
        "COMETAPI": os.environ.get("COMETAPI_KEY", ""),
    }
    
    for provider, key in api_keys.items():
        if key:  # Only validate if present
            try:
                validate_api_key(key, provider)
                config[f"{provider}_CONFIGURED"] = True
            except ConfigurationError as e:
                errors.append(str(e))
                config[f"{provider}_CONFIGURED"] = False
        else:
            config[f"{provider}_CONFIGURED"] = False
    
    # Warn about missing keys
    if not any(config.get(f"{k}_CONFIGURED") for k in api_keys.keys()):
        errors.append(
            "Warning: No API keys configured. "
            "Set at least one of: OPENROUTER_API_KEY, DASHSCOPE_API_KEY, "
            "DEEPSEEK_API_KEY, or COMETAPI_KEY"
        )
    
    if errors:
        # Log warnings but don't fail - agent can still work with local tools
        import logging
        logging.getLogger("claw_agent").warning(
            "Configuration issues: %s", "; ".join(errors)
        )
    
    return config
