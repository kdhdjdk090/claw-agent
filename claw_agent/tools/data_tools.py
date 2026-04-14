"""Data tools — CSV parsing, basic statistics, JSON querying."""

from __future__ import annotations

import csv
import io
import json
import os
import statistics
from pathlib import Path


def parse_csv(file_path: str, limit: int = 50, delimiter: str = ",") -> str:
    """Read a CSV file and return first N rows as formatted text.

    Args:
        file_path: Path to .csv or .tsv file.
        limit: Max rows to display (default 50).
        delimiter: Column separator (default comma; use '\\t' for TSV).
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    if delimiter == "\\t" or delimiter == "tab":
        delimiter = "\t"

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter=delimiter)
            rows = []
            for i, row in enumerate(reader):
                if i > limit:
                    break
                rows.append(row)

        if not rows:
            return f"CSV: {path.name} — empty file"

        # Calculate column widths for pretty printing
        col_count = max(len(r) for r in rows)
        widths = [0] * col_count
        for row in rows:
            for j, cell in enumerate(row):
                widths[j] = max(widths[j], min(len(str(cell)), 40))

        lines = [f"CSV: {path.name} (showing {min(limit, len(rows))} rows)\n"]
        for i, row in enumerate(rows):
            cells = [str(c).ljust(widths[j])[:40] for j, c in enumerate(row)]
            lines.append(" | ".join(cells))
            if i == 0:
                lines.append("-+-".join("-" * w for w in widths))

        total_reader_count = sum(1 for _ in open(path, encoding="utf-8", errors="replace")) - 1
        if total_reader_count > limit:
            lines.append(f"\n... {total_reader_count - limit} more rows not shown")

        return "\n".join(lines)
    except Exception as exc:
        return f"Error parsing CSV: {exc}"


def csv_stats(file_path: str, column: str = "") -> str:
    """Compute basic statistics for a CSV column (or all numeric columns).

    Returns count, mean, median, stdev, min, max for each numeric column.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            data: dict[str, list[float]] = {h: [] for h in headers}
            row_count = 0
            for row in reader:
                row_count += 1
                for h in headers:
                    val = row.get(h, "").strip()
                    try:
                        data[h].append(float(val.replace(",", "")))
                    except (ValueError, TypeError):
                        pass

        target_cols = [column] if column and column in headers else headers
        lines = [f"CSV Stats: {path.name} ({row_count} rows, {len(headers)} columns)\n"]

        for col in target_cols:
            nums = data.get(col, [])
            if not nums:
                continue
            lines.append(f"  {col}:")
            lines.append(f"    count  = {len(nums)}")
            lines.append(f"    mean   = {statistics.mean(nums):.4f}")
            lines.append(f"    median = {statistics.median(nums):.4f}")
            if len(nums) >= 2:
                lines.append(f"    stdev  = {statistics.stdev(nums):.4f}")
            lines.append(f"    min    = {min(nums):.4f}")
            lines.append(f"    max    = {max(nums):.4f}")
            lines.append("")

        if len(lines) <= 2:
            lines.append("No numeric columns found.")
        return "\n".join(lines)
    except Exception as exc:
        return f"Error computing stats: {exc}"


def json_query(file_path_or_text: str, query: str = "") -> str:
    """Read JSON from a file or raw text and optionally extract a nested key path.

    Query supports dot-notation: 'data.items.0.name' to traverse nested structures.
    """
    # Try file first
    data = None
    source = "input"
    path = Path(file_path_or_text).expanduser().resolve()
    if path.exists() and path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            source = path.name
        except Exception as exc:
            return f"Error reading JSON file: {exc}"
    else:
        try:
            data = json.loads(file_path_or_text)
        except json.JSONDecodeError as exc:
            return f"Error parsing JSON: {exc}"

    if not query:
        pretty = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        if len(pretty) > 10000:
            pretty = pretty[:10000] + "\n... (truncated)"
        return f"JSON ({source}):\n{pretty}"

    # Navigate query path
    current = data
    parts = query.split(".")
    for part in parts:
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                return f"Key not found: '{part}' at path '{query}'"
        elif isinstance(current, (list, tuple)):
            try:
                idx = int(part)
                current = current[idx]
            except (ValueError, IndexError):
                return f"Invalid index: '{part}' at path '{query}'"
        else:
            return f"Cannot traverse into {type(current).__name__} at '{part}'"

    pretty = json.dumps(current, indent=2, ensure_ascii=False, default=str)
    return f"Query '{query}' result:\n{pretty}"
