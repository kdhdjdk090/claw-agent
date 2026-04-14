"""SQL tools — SQLite operations for quick data work."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


def sql_run(db_path: str, sql: str) -> str:
    """Execute a SQL query on a SQLite database and return results.

    Supports both read (SELECT) and write (INSERT/UPDATE/CREATE/etc.) queries.
    Returns rows as a formatted table for SELECT, or row-count for writes.
    """
    db = Path(db_path).expanduser().resolve()
    if not db.exists() and not sql.strip().upper().startswith("CREATE"):
        return f"Database not found: {db_path}"

    try:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)

        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = cur.fetchmany(200)
            if not rows:
                return f"Query returned 0 rows.  Columns: {', '.join(cols)}"

            # Format as aligned table
            data = [cols] + [list(r) for r in rows]
            widths = [max(len(str(cell)) for cell in col) for col in zip(*data)]
            widths = [min(w, 40) for w in widths]

            lines: list[str] = []
            for i, row in enumerate(data[:52]):
                cells = [str(c)[:40].ljust(w) for c, w in zip(row, widths)]
                lines.append(" | ".join(cells))
                if i == 0:
                    lines.append("-+-".join("-" * w for w in widths))

            total = cur.rowcount if cur.rowcount >= 0 else len(rows)
            result = "\n".join(lines)
            if len(rows) == 200:
                result += f"\n... (showing first 200 of possibly more rows)"
            else:
                result += f"\n({total} row(s))"
            conn.close()
            return result
        else:
            conn.commit()
            conn.close()
            return f"Query executed successfully. Rows affected: {cur.rowcount}"

    except sqlite3.Error as exc:
        return f"SQLite error: {exc}"


def sql_tables(db_path: str) -> str:
    """Show the schema (tables, columns, types) of a SQLite database."""
    db = Path(db_path).expanduser().resolve()
    if not db.exists():
        return f"Database not found: {db_path}"

    try:
        conn = sqlite3.connect(str(db))
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]

        if not tables:
            conn.close()
            return f"Database {db.name} has no tables."

        parts: list[str] = [f"Database: {db.name}  ({len(tables)} table(s))\n"]

        for tbl in tables:
            cur.execute(f"PRAGMA table_info('{tbl}')")
            cols = cur.fetchall()
            cur.execute(f"SELECT COUNT(*) FROM '{tbl}'")
            count = cur.fetchone()[0]

            parts.append(f"TABLE {tbl}  ({count} rows)")
            for col in cols:
                _cid, name, ctype, notnull, default, pk = col
                flags = []
                if pk:
                    flags.append("PK")
                if notnull:
                    flags.append("NOT NULL")
                if default is not None:
                    flags.append(f"DEFAULT {default}")
                flag_str = f"  [{', '.join(flags)}]" if flags else ""
                parts.append(f"  {name} {ctype}{flag_str}")
            parts.append("")

        conn.close()
        return "\n".join(parts)

    except sqlite3.Error as exc:
        return f"SQLite error: {exc}"


def csv_to_sqlite(csv_path: str, db_path: str, table_name: str = "") -> str:
    """Import a CSV file into a SQLite table.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file to import.
    db_path : str
        Path to the SQLite database (created if not exists).
    table_name : str
        Table name to import into (defaults to CSV filename without extension).
    """
    cp = Path(csv_path).expanduser().resolve()
    if not cp.exists():
        return f"CSV file not found: {csv_path}"

    tbl = table_name.strip() or cp.stem
    tbl = "".join(c if c.isalnum() or c == "_" else "_" for c in tbl)

    try:
        with open(str(cp), newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers:
                return "CSV file is empty or has no header row."

            # Sanitize column names
            cols = ["".join(c if c.isalnum() or c == "_" else "_" for c in h) or f"col{i}"
                    for i, h in enumerate(headers)]

            db = Path(db_path).expanduser().resolve()
            conn = sqlite3.connect(str(db))
            cur = conn.cursor()

            col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
            cur.execute(f'CREATE TABLE IF NOT EXISTS "{tbl}" ({col_defs})')

            placeholders = ", ".join("?" * len(cols))
            row_count = 0
            batch: list[tuple] = []
            for row in reader:
                # Pad or trim row to match column count
                padded = (row + [""] * len(cols))[:len(cols)]
                batch.append(tuple(padded))
                row_count += 1
                if len(batch) >= 500:
                    cur.executemany(f'INSERT INTO "{tbl}" VALUES ({placeholders})', batch)
                    batch.clear()

            if batch:
                cur.executemany(f'INSERT INTO "{tbl}" VALUES ({placeholders})', batch)

            conn.commit()
            conn.close()
            return f"Imported {row_count} rows into {tbl} ({len(cols)} columns) in {db.name}"

    except (csv.Error, sqlite3.Error, UnicodeDecodeError) as exc:
        return f"Import error: {exc}"
