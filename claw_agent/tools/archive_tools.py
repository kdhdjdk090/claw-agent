"""Archive tools — create and extract zip / tar / gz archives."""

from __future__ import annotations

import os
import shutil
import tarfile
import zipfile
from pathlib import Path


def create_archive(
    source: str,
    output: str = "",
    format: str = "zip",
) -> str:
    """Create a zip or tar.gz archive.

    Args:
        source: File or directory to archive.
        output: Output path. Defaults to source name + extension.
        format: 'zip', 'tar', 'tar.gz', or 'tar.bz2'.
    """
    src = Path(source).expanduser().resolve()
    if not src.exists():
        return f"Error: source not found — {source}"

    ext_map = {"zip": ".zip", "tar": ".tar", "tar.gz": ".tar.gz", "tar.bz2": ".tar.bz2"}
    if format not in ext_map:
        return f"Error: unsupported format '{format}'. Use zip, tar, tar.gz, or tar.bz2."

    if not output:
        output = str(src) + ext_map[format]
    out = Path(output).expanduser().resolve()

    try:
        if format == "zip":
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
                if src.is_file():
                    zf.write(src, src.name)
                else:
                    for fp in src.rglob("*"):
                        if fp.is_file():
                            zf.write(fp, fp.relative_to(src.parent))
            count = len(zipfile.ZipFile(out).namelist())
        else:
            mode = {"tar": "w", "tar.gz": "w:gz", "tar.bz2": "w:bz2"}[format]
            with tarfile.open(out, mode) as tf:
                tf.add(str(src), arcname=src.name)
            count = "?"

        size = out.stat().st_size
        size_str = f"{size / 1024:.1f} KB" if size < 1_048_576 else f"{size / 1_048_576:.1f} MB"
        return f"✅ Created {format} archive: {out}\n   Size: {size_str}, entries: {count}"

    except Exception as e:
        return f"Error creating archive: {type(e).__name__}: {e}"


def extract_archive(
    archive: str,
    destination: str = "",
) -> str:
    """Extract a zip, tar, tar.gz, or tar.bz2 archive.

    Args:
        archive: Path to archive file.
        destination: Directory to extract into. Defaults to archive name without extension.
    """
    arc = Path(archive).expanduser().resolve()
    if not arc.is_file():
        return f"Error: file not found — {archive}"

    if not destination:
        # Strip extension(s)
        name = arc.stem
        if name.endswith(".tar"):
            name = name[:-4]
        destination = str(arc.parent / name)
    dest = Path(destination).expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    try:
        suffix = arc.suffix.lower()
        suffixes = "".join(s.lower() for s in arc.suffixes)

        if suffix == ".zip":
            with zipfile.ZipFile(arc, "r") as zf:
                # Security: prevent path traversal
                for member in zf.namelist():
                    target = (dest / member).resolve()
                    if not str(target).startswith(str(dest)):
                        return f"Error: archive contains path traversal — {member}"
                zf.extractall(dest)
                count = len(zf.namelist())
        elif suffix in (".tar", ".gz", ".bz2", ".xz") or ".tar" in suffixes:
            with tarfile.open(arc, "r:*") as tf:
                # Security: prevent path traversal
                for member in tf.getmembers():
                    target = (dest / member.name).resolve()
                    if not str(target).startswith(str(dest)):
                        return f"Error: archive contains path traversal — {member.name}"
                tf.extractall(dest, filter="data")
                count = len(tf.getmembers())
        else:
            return f"Error: unrecognized archive format '{suffix}'"

        return f"✅ Extracted {count} entries to: {dest}"

    except Exception as e:
        return f"Error extracting archive: {type(e).__name__}: {e}"
