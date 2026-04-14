"""Regex tools — test patterns, explain regex in plain English."""

from __future__ import annotations

import re


def test_regex(pattern: str, text: str, flags: str = "") -> str:
    """Test a regex pattern against text and show all matches.

    Args:
        pattern: Regular expression pattern.
        text: Text to search.
        flags: Optional flags string — 'i' (ignore case), 'm' (multiline),
               's' (dotall), 'x' (verbose). Combine: 'im'.
    """
    # Build flags
    flag_map = {
        "i": re.IGNORECASE,
        "m": re.MULTILINE,
        "s": re.DOTALL,
        "x": re.VERBOSE,
    }
    re_flags = 0
    for ch in flags.lower():
        if ch in flag_map:
            re_flags |= flag_map[ch]

    try:
        compiled = re.compile(pattern, re_flags)
    except re.error as exc:
        return f"Regex error: {exc}"

    matches = list(compiled.finditer(text))
    if not matches:
        return f"Pattern: /{pattern}/{flags}\nNo matches found in text ({len(text)} chars)."

    lines = [
        f"Pattern: /{pattern}/{flags}",
        f"Matches: {len(matches)}",
        "",
    ]

    for i, m in enumerate(matches[:50]):
        groups_str = ""
        if m.groups():
            groups_str = "  groups: " + str(m.groups())
        if m.groupdict():
            named = {k: v for k, v in m.groupdict().items() if v is not None}
            if named:
                groups_str += f"  named: {named}"

        lines.append(f"  [{i}] pos {m.start()}-{m.end()}: '{m.group()}'{groups_str}")

    if len(matches) > 50:
        lines.append(f"  ... and {len(matches) - 50} more matches")

    return "\n".join(lines)


def explain_regex(pattern: str) -> str:
    """Explain a regex pattern in plain English.

    Breaks down each component of the pattern into human-readable descriptions.
    """
    explanations = {
        r".": "any character (except newline)",
        r"^": "start of string/line",
        r"$": "end of string/line",
        r"*": "0 or more of previous",
        r"+": "1 or more of previous",
        r"?": "0 or 1 of previous (optional)",
        r"\d": "any digit (0-9)",
        r"\D": "any non-digit",
        r"\w": "any word character (letter, digit, underscore)",
        r"\W": "any non-word character",
        r"\s": "any whitespace (space, tab, newline)",
        r"\S": "any non-whitespace",
        r"\b": "word boundary",
        r"\B": "non-word boundary",
        r"\n": "newline",
        r"\t": "tab",
        r"|": "OR (alternation)",
    }

    lines = [f"Pattern: /{pattern}/", ""]

    # Validate
    try:
        re.compile(pattern)
    except re.error as exc:
        lines.append(f"⚠ Invalid regex: {exc}")
        return "\n".join(lines)

    # Walk through the pattern
    i = 0
    position = 0
    parts = []

    while i < len(pattern):
        ch = pattern[i]

        if ch == "\\" and i + 1 < len(pattern):
            seq = pattern[i : i + 2]
            desc = explanations.get(seq, f"escaped '{pattern[i+1]}'")
            parts.append((seq, desc))
            i += 2
        elif ch == "[":
            # Character class
            end = pattern.find("]", i + 1)
            if end == -1:
                end = len(pattern) - 1
            cls = pattern[i : end + 1]
            neg = "NOT " if len(cls) > 1 and cls[1] == "^" else ""
            inner = cls[2:-1] if neg else cls[1:-1]
            parts.append((cls, f"{neg}any of: {inner}"))
            i = end + 1
        elif ch == "(":
            # Group
            if i + 1 < len(pattern) and pattern[i + 1] == "?":
                if i + 2 < len(pattern):
                    if pattern[i + 2] == ":":
                        parts.append(("(?:", "non-capturing group"))
                        i += 3
                        continue
                    elif pattern[i + 2] == "P" and i + 3 < len(pattern) and pattern[i + 3] == "<":
                        end = pattern.find(">", i + 4)
                        name = pattern[i + 4 : end] if end > i + 4 else "?"
                        parts.append((pattern[i : end + 1], f"named group '{name}'"))
                        i = end + 1
                        continue
                    elif pattern[i + 2] == "=":
                        parts.append(("(?=", "lookahead"))
                        i += 3
                        continue
                    elif pattern[i + 2] == "!":
                        parts.append(("(?!", "negative lookahead"))
                        i += 3
                        continue
            parts.append(("(", "start capturing group"))
            i += 1
        elif ch == ")":
            parts.append((")", "end group"))
            i += 1
        elif ch == "{":
            end = pattern.find("}", i)
            if end != -1:
                quant = pattern[i : end + 1]
                inner = quant[1:-1]
                if "," in inner:
                    lo, hi = inner.split(",", 1)
                    hi = hi.strip()
                    if hi:
                        parts.append((quant, f"between {lo} and {hi} times"))
                    else:
                        parts.append((quant, f"{lo} or more times"))
                else:
                    parts.append((quant, f"exactly {inner} times"))
                i = end + 1
            else:
                parts.append((ch, "literal '{'"))
                i += 1
        elif ch in explanations:
            parts.append((ch, explanations[ch]))
            i += 1
        else:
            parts.append((ch, f"literal '{ch}'"))
            i += 1

    lines.append("Breakdown:")
    for token, desc in parts:
        lines.append(f"  {token:15s} → {desc}")

    # Groups count
    try:
        compiled = re.compile(pattern)
        n_groups = compiled.groups
        if n_groups:
            lines.append(f"\nCapturing groups: {n_groups}")
        named = compiled.groupindex
        if named:
            lines.append(f"Named groups: {dict(named)}")
    except Exception:
        pass

    return "\n".join(lines)
