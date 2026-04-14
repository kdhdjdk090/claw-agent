"""Hashing, checksum, and encoding/decoding tools."""

from __future__ import annotations

import base64
import hashlib
import os
import urllib.parse


def compute_hash(
    target: str,
    algorithm: str = "sha256",
    is_file: bool = False,
) -> str:
    """Compute a cryptographic hash.

    Args:
        target: A file path (if is_file=True) or a string to hash.
        algorithm: Hash algorithm — sha256, sha1, md5, sha512, sha384.
        is_file: If True, hash the file at *target* path.
    """
    algo = algorithm.lower().replace("-", "")
    if algo not in {"sha256", "sha1", "md5", "sha512", "sha384"}:
        return f"Unsupported algorithm: {algorithm}. Use sha256, sha1, md5, sha512, sha384."

    try:
        h = hashlib.new(algo)
        if is_file:
            path = os.path.abspath(target)
            if not os.path.isfile(path):
                return f"File not found: {path}"
            size = os.path.getsize(path)
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return (
                f"Algorithm : {algo}\n"
                f"File      : {path}\n"
                f"Size      : {size:,} bytes\n"
                f"Hash      : {h.hexdigest()}"
            )
        else:
            h.update(target.encode("utf-8"))
            return (
                f"Algorithm : {algo}\n"
                f"Input     : {target[:120]}{'…' if len(target) > 120 else ''}\n"
                f"Hash      : {h.hexdigest()}"
            )

    except Exception as e:
        return f"Error computing hash: {type(e).__name__}: {e}"


def encode_decode(
    text: str,
    encoding: str = "base64",
    decode: bool = False,
) -> str:
    """Encode or decode text using various schemes.

    Args:
        text: The text to encode/decode.
        encoding: Encoding scheme — base64, url, hex.
        decode: If True, decode instead of encode.
    """
    enc = encoding.lower().replace("-", "").replace("_", "")

    try:
        if enc == "base64":
            if decode:
                result = base64.b64decode(text).decode("utf-8", errors="replace")
            else:
                result = base64.b64encode(text.encode("utf-8")).decode("ascii")

        elif enc in {"url", "urlencode", "percent"}:
            if decode:
                result = urllib.parse.unquote(text)
            else:
                result = urllib.parse.quote(text, safe="")

        elif enc == "hex":
            if decode:
                result = bytes.fromhex(text).decode("utf-8", errors="replace")
            else:
                result = text.encode("utf-8").hex()

        else:
            return f"Unsupported encoding: {encoding}. Use base64, url, hex."

        action = "Decoded" if decode else "Encoded"
        return (
            f"{action} ({encoding}):\n"
            f"Input  : {text[:200]}{'…' if len(text) > 200 else ''}\n"
            f"Result : {result[:2000]}{'…' if len(result) > 2000 else ''}"
        )

    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
