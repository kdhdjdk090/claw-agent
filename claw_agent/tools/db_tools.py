"""Database tools — SQLite query execution and schema inspection."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path


def sqlite_query(db_path: str, query: str, params: str = "[]") -> str:
    """Execute a SQL query against a SQLite database.

    For SELECT queries, returns results as a formatted table.
    For INSERT/UPDATE/DELETE, returns affected row count.
    Parameterized queries supported via JSON params array.

    Args:
        db_path: Path to .db or .sqlite file. Creates if not exists.
        query: SQL query string. Use ? for parameter placeholders.
        params: JSON array of parameter values (default empty).
    """
    path = Path(db_path).expanduser().resolve()

    # Security: block obviously destructive operations on system databases
    dangerous_keywords = ["DROP DATABASE", "DROP TABLE", "TRUNCATE", "DELETE FROM sqlite_"]
    query_upper = query.upper().strip()
    for kw in dangerous_keywords:
        if kw in query_upper and "WHERE" not in query_upper:
            return f"Blocked: Potentially destructive query without WHERE clause. Query: {query}"

    try:
        param_list = json.loads(params) if params else []
    except json.JSONDecodeError:
        return f"Error: Invalid params JSON — {params}"

    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, param_list)

        if query_upper.startswith("SELECT") or query_upper.startswith("PRAGMA") or query_upper.startswith("WITH"):
            rows = cursor.fetchall()
            if not rows:
                conn.close()
                return "Query returned 0 rows."

            columns = [desc[0] for desc in cursor.description]

            # Format as table
            col_widths = [len(c) for c in columns]
            str_rows = []
            for row in rows[:200]:
                str_row = [str(row[c]) if row[c] is not None else "NULL" for c in columns]
                for i, val in enumerate(str_row):
                    col_widths[i] = max(col_widths[i], min(len(val), 50))
                str_rows.append(str_row)

            lines = []
            header = " | ".join(c.ljust(col_widths[i])[:50] for i, c in enumerate(columns))
            lines.append(header)
            lines.append("-+-".join("-" * w for w in col_widths))
            for str_row in str_rows:
                lines.append(" | ".join(v.ljust(col_widths[i])[:50] for i, v in enumerate(str_row)))

            if len(rows) > 200:
                lines.append(f"\n... showing 200 of {len(rows)} rows")

            conn.close()
            return f"Query returned {len(rows)} rows:\n\n" + "\n".join(lines)
        else:
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return f"Query executed successfully. Rows affected: {affected}"

    except sqlite3.Error as exc:
        return f"SQLite error: {exc}"
    except Exception as exc:
        return f"Error: {exc}"


def sqlite_schema(db_path: str) -> str:
    """List all tables and their columns in a SQLite database.

    Args:
        db_path: Path to .db or .sqlite file.
    """
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        return f"Error: Database not found — {db_path}"

    try:
        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            conn.close()
            return f"Database {path.name}: empty (no tables)"

        lines = [f"Database: {path.name}", f"Tables: {len(tables)}", ""]

        for table in tables:
            cursor.execute(f"PRAGMA table_info('{table}')")
            columns = cursor.fetchall()
            # Count rows
            try:
                cursor.execute(f"SELECT COUNT(*) FROM '{table}'")
                row_count = cursor.fetchone()[0]
            except Exception:
                row_count = "?"

            lines.append(f"  {table} ({row_count} rows):")
            for col in columns:
                cid, name, col_type, notnull, default, pk = col
                flags = []
                if pk:
                    flags.append("PK")
                if notnull:
                    flags.append("NOT NULL")
                if default is not None:
                    flags.append(f"DEFAULT={default}")
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                lines.append(f"    {name}: {col_type or 'ANY'}{flag_str}")
            lines.append("")

        # Also show indexes
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name")
        indexes = cursor.fetchall()
        if indexes:
            lines.append("Indexes:")
            for idx_name, tbl_name in indexes:
                lines.append(f"  {idx_name} → {tbl_name}")

        conn.close()
        return "\n".join(lines)

    except sqlite3.Error as exc:
        return f"SQLite error: {exc}"
    except Exception as exc:
        return f"Error: {exc}"
