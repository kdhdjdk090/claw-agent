"""Image tools — view and analyze image files."""

from __future__ import annotations

import base64
import os
from pathlib import Path


SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".svg"}


def view_image(file_path: str) -> str:
    """View/analyze an image file. Returns metadata and base64 data URI.

    Supports: png, jpg, jpeg, gif, webp, bmp, tiff, svg
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    ext = path.suffix.lower()
    if ext not in SUPPORTED_IMAGE_EXTS:
        return f"Error: Unsupported format '{ext}'. Supported: {', '.join(sorted(SUPPORTED_IMAGE_EXTS))}"

    size_bytes = path.stat().st_size
    size_kb = size_bytes / 1024

    # MIME mapping
    mime_map = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
        ".tiff": "image/tiff", ".svg": "image/svg+xml",
    }
    mime = mime_map.get(ext, "application/octet-stream")

    info_lines = [
        f"Image: {path.name}",
        f"Path: {path}",
        f"Format: {ext[1:].upper()}",
        f"Size: {size_kb:.1f} KB ({size_bytes:,} bytes)",
        f"MIME: {mime}",
    ]

    # Try to get dimensions with PIL if available
    try:
        from PIL import Image
        with Image.open(path) as img:
            w, h = img.size
            info_lines.append(f"Dimensions: {w}×{h}")
            info_lines.append(f"Mode: {img.mode}")
            if hasattr(img, "n_frames") and img.n_frames > 1:
                info_lines.append(f"Frames: {img.n_frames}")
    except ImportError:
        info_lines.append("(Install Pillow for dimension info)")
    except Exception:
        pass

    # Encode as base64 data URI for multimodal models
    if size_bytes < 5 * 1024 * 1024:  # < 5 MB
        raw = path.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        info_lines.append(f"\nData URI: data:{mime};base64,{b64[:100]}...")
        info_lines.append(f"Base64 length: {len(b64):,} chars")
    else:
        info_lines.append("(File too large for base64 embedding)")

    return "\n".join(info_lines)


def list_images(directory: str = ".") -> str:
    """List all image files in a directory recursively."""
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: Not a directory — {directory}"

    images = []
    for f in sorted(root.rglob("*")):
        if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTS:
            rel = f.relative_to(root)
            size_kb = f.stat().st_size / 1024
            images.append(f"  {rel}  ({size_kb:.1f} KB)")

    if not images:
        return f"No images found in {root}"
    return f"Images in {root} ({len(images)} files):\n" + "\n".join(images)
