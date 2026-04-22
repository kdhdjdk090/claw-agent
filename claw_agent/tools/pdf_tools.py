"""PDF tools — read text, extract metadata from PDF files."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# Allowed modules for PDF processing - security allowlist
ALLOWED_PDF_MODULES = {"pypdf", "PyPDF2", "pdfminer", "pdfminer.six"}


def _safe_import_pdf_module(mod_name: str):
    """Safely import a PDF processing module from allowlist.
    
    Args:
        mod_name: Name of the module to import
        
    Returns:
        Imported module or None if not available
        
    Raises:
        ImportError: If module is not in allowlist
    """
    if mod_name not in ALLOWED_PDF_MODULES:
        raise ImportError(
            f"Module '{mod_name}' is not in the allowed PDF modules: {ALLOWED_PDF_MODULES}"
        )
    
    try:
        import importlib
        return importlib.import_module(mod_name)
    except ImportError:
        return None


def read_pdf(file_path: str, pages: str = "") -> str:
    """Extract text from a PDF file. Optionally specify pages like '1-3' or '1,3,5'.

    Tries PyPDF2/pypdf first, falls back to pdfminer, then to pdftotext CLI.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"
    if path.suffix.lower() != ".pdf":
        return f"Error: Not a PDF file — {path.suffix}"

    # Parse page spec
    target_pages: set[int] | None = None
    if pages:
        target_pages = set()
        for part in pages.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                target_pages.update(range(int(a), int(b) + 1))
            else:
                target_pages.add(int(part))

    # Try pypdf (modern) or PyPDF2 using safe import
    for mod_name in ("pypdf", "PyPDF2"):
        mod = _safe_import_pdf_module(mod_name)
        if mod is None:
            continue
            
        try:
            reader = mod.PdfReader(str(path))
            total = len(reader.pages)
            texts = []
            for i, page in enumerate(reader.pages):
                page_num = i + 1
                if target_pages and page_num not in target_pages:
                    continue
                text = page.extract_text() or ""
                if text.strip():
                    texts.append(f"--- Page {page_num} ---\n{text}")
            if texts:
                header = f"PDF: {path.name} ({total} pages)\n\n"
                return header + "\n\n".join(texts)
            return f"PDF: {path.name} ({total} pages) — no extractable text (scanned/image PDF?)"
        except Exception as exc:
            return f"Error reading PDF with {mod_name}: {exc}"

    # Fallback: pdfminer.six
    try:
        from pdfminer.high_level import extract_text
        from pdfminer.pdfparser import PDFParser
        from pdfminer.pdfdocument import PDFDocument
        
        with open(path, 'rb') as f:
            parser = PDFParser(f)
            doc = PDFDocument(parser)
            total = len(list(doc.getpages()))
        
        text = extract_text(str(path))
        if text and text.strip():
            return f"PDF: {path.name} ({total} pages)\n\n{text}"
        return f"PDF: {path.name} ({total} pages) — no extractable text"
    except ImportError:
        pass
    except Exception as exc:
        return f"Error reading PDF with pdfminer: {exc}"

    # Fallback: pdftotext CLI (poppler-utils)
    try:
        cmd = ["pdftotext", str(path), "-"]
        if pages:
            # pdftotext supports -f (first) -l (last)
            pass
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return f"PDF: {path.name}\n\n{result.stdout}"
    except FileNotFoundError:
        pass
    except Exception:
        pass

    return (
        f"Error: Could not extract text from {path.name}.\n"
        "Install pypdf: pip install pypdf\n"
        "Or install poppler-utils for pdftotext CLI."
    )


def pdf_info(file_path: str) -> str:
    """Get PDF metadata — page count, author, title, creation date, file size."""
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    size_kb = path.stat().st_size / 1024
    info_lines = [
        f"PDF: {path.name}",
        f"Path: {path}",
        f"Size: {size_kb:.1f} KB",
    ]

    for mod_name in ("pypdf", "PyPDF2"):
        try:
            mod = __import__(mod_name)
            reader = mod.PdfReader(str(path))
            info_lines.append(f"Pages: {len(reader.pages)}")
            meta = reader.metadata
            if meta:
                for key in ("/Title", "/Author", "/Subject", "/Creator", "/Producer", "/CreationDate"):
                    val = meta.get(key)
                    if val:
                        info_lines.append(f"{key[1:]}: {val}")
            return "\n".join(info_lines)
        except ImportError:
            continue
        except Exception as exc:
            info_lines.append(f"Metadata error: {exc}")
            return "\n".join(info_lines)

    info_lines.append("(Install pypdf for full metadata: pip install pypdf)")
    return "\n".join(info_lines)
