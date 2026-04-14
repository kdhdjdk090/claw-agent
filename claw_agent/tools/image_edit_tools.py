"""Image editing tools — resize, crop, convert, thumbnail."""

from __future__ import annotations

import os
from pathlib import Path


def resize_image(file_path: str, width: int = 0, height: int = 0, output: str = "") -> str:
    """Resize an image. Specify width, height, or both. Maintains aspect ratio if only one given."""
    try:
        from PIL import Image
    except ImportError:
        return "Error: Pillow not installed. Run: pip install Pillow"

    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    if width <= 0 and height <= 0:
        return "Error: Provide at least width or height (positive integer)."

    with Image.open(path) as img:
        orig_w, orig_h = img.size

        if width > 0 and height > 0:
            new_size = (width, height)
        elif width > 0:
            ratio = width / orig_w
            new_size = (width, int(orig_h * ratio))
        else:
            ratio = height / orig_h
            new_size = (int(orig_w * ratio), height)

        resized = img.resize(new_size, Image.LANCZOS)
        out_path = Path(output) if output else path.with_stem(f"{path.stem}_resized")
        resized.save(out_path)
        return f"Resized {orig_w}×{orig_h} → {new_size[0]}×{new_size[1]}\nSaved: {out_path}"


def crop_image(file_path: str, left: int = 0, top: int = 0, right: int = 0, bottom: int = 0, output: str = "") -> str:
    """Crop an image. Provide left, top, right, bottom pixel coordinates."""
    try:
        from PIL import Image
    except ImportError:
        return "Error: Pillow not installed. Run: pip install Pillow"

    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    with Image.open(path) as img:
        w, h = img.size
        r = right if right > 0 else w
        b = bottom if bottom > 0 else h

        if left >= r or top >= b:
            return f"Error: Invalid crop box ({left},{top},{r},{b}) for image {w}×{h}"

        cropped = img.crop((left, top, r, b))
        out_path = Path(output) if output else path.with_stem(f"{path.stem}_cropped")
        cropped.save(out_path)
        return f"Cropped ({left},{top},{r},{b}) from {w}×{h}\nResult: {r-left}×{b-top}\nSaved: {out_path}"


def convert_image(file_path: str, format: str = "png", output: str = "") -> str:
    """Convert image to another format (png, jpg, webp, bmp, gif, tiff)."""
    try:
        from PIL import Image
    except ImportError:
        return "Error: Pillow not installed. Run: pip install Pillow"

    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    fmt = format.lower().strip(".")
    ext_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP",
               "bmp": "BMP", "gif": "GIF", "tiff": "TIFF"}
    pil_fmt = ext_map.get(fmt)
    if not pil_fmt:
        return f"Error: Unsupported format '{fmt}'. Supported: {', '.join(ext_map.keys())}"

    with Image.open(path) as img:
        if pil_fmt == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        out_ext = ".jpg" if fmt in ("jpg", "jpeg") else f".{fmt}"
        out_path = Path(output) if output else path.with_suffix(out_ext)
        img.save(out_path, pil_fmt)
        size_kb = out_path.stat().st_size / 1024
        return f"Converted {path.suffix} → {out_ext} ({size_kb:.1f} KB)\nSaved: {out_path}"


def create_thumbnail(file_path: str, size: int = 128, output: str = "") -> str:
    """Create a square thumbnail of the given size (default 128px)."""
    try:
        from PIL import Image
    except ImportError:
        return "Error: Pillow not installed. Run: pip install Pillow"

    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    with Image.open(path) as img:
        img.thumbnail((size, size), Image.LANCZOS)
        out_path = Path(output) if output else path.with_stem(f"{path.stem}_thumb")
        img.save(out_path)
        return f"Thumbnail {size}×{size} created\nSaved: {out_path}"
