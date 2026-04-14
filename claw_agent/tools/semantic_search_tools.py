"""Semantic search — natural language codebase search using TF-IDF."""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from pathlib import Path


# Extensions worth indexing
CODE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".kt", ".scala",
    ".php", ".lua", ".sh", ".bash", ".zsh", ".ps1", ".sql",
    ".html", ".css", ".scss", ".less", ".vue", ".svelte",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".md", ".txt", ".rst",
}

IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "dist",
    "build", ".next", ".nuxt", "target", "bin", "obj", ".tox",
}


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase alphanumeric tokens."""
    return re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower())


def _should_index(path: Path) -> bool:
    parts = set(path.parts)
    return (
        path.suffix.lower() in CODE_EXTS
        and not parts.intersection(IGNORE_DIRS)
        and path.stat().st_size < 500_000  # skip huge files
    )


def semantic_search(query: str, directory: str = ".", max_results: int = 10) -> str:
    """Search the codebase using natural language. Returns relevant code snippets.

    Uses TF-IDF scoring for fast, dependency-free semantic matching.
    """
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: Not a directory — {directory}"

    query_tokens = _tokenize(query)
    if not query_tokens:
        return "Error: Query produced no searchable tokens."

    # Index files
    doc_tokens: dict[Path, list[str]] = {}
    for f in root.rglob("*"):
        if f.is_file() and _should_index(f):
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                tokens = _tokenize(text)
                if tokens:
                    doc_tokens[f] = tokens
            except Exception:
                continue

    if not doc_tokens:
        return f"No indexable source files found in {root}"

    # Compute IDF
    N = len(doc_tokens)
    df: Counter[str] = Counter()
    for tokens in doc_tokens.values():
        df.update(set(tokens))
    idf = {t: math.log(N / (df[t] + 1)) for t in set(query_tokens) if df.get(t, 0) > 0}

    # Score each document by TF-IDF of query terms
    scores: list[tuple[float, Path]] = []
    for path, tokens in doc_tokens.items():
        tf = Counter(tokens)
        total = len(tokens)
        score = sum(
            (tf.get(qt, 0) / total) * idf.get(qt, 0)
            for qt in query_tokens
        )
        if score > 0:
            scores.append((score, path))

    scores.sort(key=lambda x: -x[0])
    top = scores[:max_results]

    if not top:
        return f"No matches for '{query}' in {root}"

    # Format results with snippets
    results = [f"Semantic search: '{query}' ({len(scores)} matches, showing top {len(top)})"]
    results.append("")

    for rank, (score, path) in enumerate(top, 1):
        rel = path.relative_to(root)
        results.append(f"--- [{rank}] {rel} (score: {score:.4f}) ---")

        # Extract best snippet: find the paragraph with most query term hits
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            best_line = 0
            best_hits = 0
            for i, line in enumerate(lines):
                ltokens = set(_tokenize(line))
                hits = len(ltokens.intersection(query_tokens))
                if hits > best_hits:
                    best_hits = hits
                    best_line = i

            start = max(0, best_line - 2)
            end = min(len(lines), best_line + 5)
            snippet = "\n".join(f"  {start+j+1:4d} | {lines[start+j]}" for j in range(end - start))
            results.append(snippet)
        except Exception:
            results.append("  (could not read snippet)")
        results.append("")

    return "\n".join(results)
