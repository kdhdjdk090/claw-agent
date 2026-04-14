"""Crypto tools — token generation, hashing, encoding."""

from __future__ import annotations

import base64
import hashlib
import secrets
import string


def generate_token(length: int = 32, charset: str = "hex") -> str:
    """Generate a cryptographically secure random token.

    Args:
        length: Token length (default 32).
        charset: "hex", "alphanumeric", "base64", "urlsafe", "digits", "password".
    """
    length = min(max(length, 4), 256)

    if charset == "hex":
        return secrets.token_hex(length // 2 + 1)[:length]
    elif charset == "base64":
        raw = secrets.token_bytes(length)
        return base64.b64encode(raw).decode("ascii")[:length]
    elif charset == "urlsafe":
        return secrets.token_urlsafe(length)[:length]
    elif charset == "digits":
        return "".join(secrets.choice(string.digits) for _ in range(length))
    elif charset == "alphanumeric":
        alpha = string.ascii_letters + string.digits
        return "".join(secrets.choice(alpha) for _ in range(length))
    elif charset == "password":
        # Ensure at least one of each category
        cats = [string.ascii_lowercase, string.ascii_uppercase, string.digits, "!@#$%^&*()-_=+"]
        pwd = [secrets.choice(c) for c in cats]
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        pwd += [secrets.choice(all_chars) for _ in range(length - len(pwd))]
        # Shuffle in-place
        pwd_list = list(pwd)
        for i in range(len(pwd_list) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            pwd_list[i], pwd_list[j] = pwd_list[j], pwd_list[i]
        return "".join(pwd_list)
    else:
        return f"Error: Unknown charset '{charset}'. Supported: hex, alphanumeric, base64, urlsafe, digits, password"


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Hash a string with the specified algorithm.

    Args:
        text: String to hash.
        algorithm: "sha256", "sha512", "sha1", "md5", "blake2b".
    """
    algos = {
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
        "sha1": hashlib.sha1,
        "md5": hashlib.md5,
        "blake2b": hashlib.blake2b,
    }
    fn = algos.get(algorithm.lower())
    if not fn:
        return f"Error: Unknown algorithm '{algorithm}'. Supported: {', '.join(algos)}"

    digest = fn(text.encode("utf-8")).hexdigest()
    return f"{algorithm.upper()}: {digest}"


def base64_codec(text: str, operation: str = "encode") -> str:
    """Encode or decode base64.

    Args:
        text: Input text.
        operation: "encode" or "decode".
    """
    if operation == "encode":
        result = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return f"Base64 encoded:\n{result}"
    elif operation == "decode":
        try:
            # Handle URL-safe variant and padding
            padded = text.strip()
            padded += "=" * (-len(padded) % 4)
            decoded = base64.b64decode(padded).decode("utf-8", errors="replace")
            return f"Base64 decoded:\n{decoded}"
        except Exception as e:
            return f"Error decoding base64: {e}"
    else:
        return f"Error: Unknown operation '{operation}'. Use 'encode' or 'decode'."


def checksum_file(file_path: str, algorithm: str = "sha256") -> str:
    """Compute a file checksum.

    Args:
        file_path: Path to the file.
        algorithm: "sha256", "sha512", "md5", "blake2b".
    """
    from pathlib import Path as P
    fp = P(file_path).expanduser().resolve()
    if not fp.is_file():
        return f"Error: File not found — {file_path}"

    algos = {"sha256": hashlib.sha256, "sha512": hashlib.sha512, "md5": hashlib.md5, "blake2b": hashlib.blake2b}
    fn = algos.get(algorithm.lower())
    if not fn:
        return f"Error: Unknown algorithm. Supported: {', '.join(algos)}"

    h = fn()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)

    size_kb = fp.stat().st_size / 1024
    return f"{fp.name} ({size_kb:.1f} KB)\n{algorithm.upper()}: {h.hexdigest()}"
