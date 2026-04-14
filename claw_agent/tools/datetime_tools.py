"""Datetime tools — timezone time, date arithmetic, cron parsing."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone, date


# ---- Timezone offsets (stdlib only, no pytz needed) ----
_TZ_OFFSETS = {
    "utc": 0, "gmt": 0, "est": -5, "edt": -4, "cst": -6, "cdt": -5,
    "mst": -7, "mdt": -6, "pst": -8, "pdt": -7, "akst": -9, "akdt": -8,
    "hst": -10, "ist": 5.5, "jst": 9, "kst": 9, "cst_cn": 8, "cet": 1,
    "cest": 2, "eet": 2, "eest": 3, "gmt+1": 1, "gmt+2": 2, "gmt+3": 3,
    "gmt+4": 4, "gmt+5": 5, "gmt+6": 6, "gmt+7": 7, "gmt+8": 8,
    "gmt+9": 9, "gmt+10": 10, "gmt+11": 11, "gmt+12": 12,
    "gmt-1": -1, "gmt-2": -2, "gmt-3": -3, "gmt-4": -4, "gmt-5": -5,
    "gmt-6": -6, "gmt-7": -7, "gmt-8": -8, "gmt-9": -9, "gmt-10": -10,
    "gmt-11": -11, "gmt-12": -12,
    "aest": 10, "aedt": 11, "awst": 8, "nzst": 12, "nzdt": 13,
    "brt": -3, "wet": 0, "west": 1, "sgt": 8, "hkt": 8, "ict": 7,
    "pht": 8, "wib": 7, "wita": 8, "wit": 9,
}


def now_tz(tz: str = "utc") -> str:
    """Get current time in a timezone.

    Args:
        tz: Timezone abbreviation (UTC, EST, PST, JST, IST, CET, etc.) or offset like '+5' or '-3.5'.
    """
    tz_key = tz.strip().lower().replace(" ", "")

    # Try direct offset like "+5" or "-3.5"
    offset_hours = None
    if re.match(r'^[+-]?\d+\.?\d*$', tz_key):
        offset_hours = float(tz_key)
    elif tz_key in _TZ_OFFSETS:
        offset_hours = _TZ_OFFSETS[tz_key]

    if offset_hours is None:
        supported = ", ".join(sorted(k.upper() for k in _TZ_OFFSETS.keys() if not k.startswith("gmt")))
        return f"Error: Unknown timezone '{tz}'. Supported: {supported}, or numeric offset like '+5', '-3.5'."

    offset = timezone(timedelta(hours=offset_hours))
    now = datetime.now(offset)
    sign = "+" if offset_hours >= 0 else ""
    tz_label = tz.upper() if tz.strip().lower() in _TZ_OFFSETS else f"UTC{sign}{offset_hours:g}"

    return (
        f"{tz_label}: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Day: {now.strftime('%A')}\n"
        f"ISO: {now.isoformat()}\n"
        f"Unix: {int(now.timestamp())}"
    )


def date_diff(date1: str, date2: str = "") -> str:
    """Calculate the difference between two dates.

    Args:
        date1: First date (YYYY-MM-DD, or 'today'/'now').
        date2: Second date (YYYY-MM-DD, or 'today'/'now'). Defaults to today.
    """
    d1 = _parse_date(date1.strip())
    d2 = _parse_date(date2.strip()) if date2.strip() else date.today()

    if isinstance(d1, str):
        return d1  # error message
    if isinstance(d2, str):
        return d2

    delta = d2 - d1
    days = abs(delta.days)

    years = days // 365
    remaining = days % 365
    months = remaining // 30
    leftover_days = remaining % 30
    weeks = days // 7

    direction = "from now" if delta.days > 0 else "ago" if delta.days < 0 else ""

    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    if leftover_days:
        parts.append(f"{leftover_days} day{'s' if leftover_days != 1 else ''}")

    human = ", ".join(parts) if parts else "same day"

    lines = [
        f"{d1.isoformat()} → {d2.isoformat()}",
        f"Days: {days} {direction}".strip(),
        f"Weeks: {weeks}",
        f"Approx: {human}",
    ]
    return "\n".join(lines)


def parse_cron(expression: str) -> str:
    """Explain a cron expression in plain English.

    Args:
        expression: Cron expression (e.g., '*/5 * * * *', '0 9 * * MON-FRI').
    """
    parts = expression.strip().split()

    # Handle predefined shortcuts
    shortcuts = {
        "@yearly": "0 0 1 1 *", "@annually": "0 0 1 1 *",
        "@monthly": "0 0 1 * *", "@weekly": "0 0 * * 0",
        "@daily": "0 0 * * *", "@midnight": "0 0 * * *",
        "@hourly": "0 * * * *",
    }
    if len(parts) == 1 and parts[0].lower() in shortcuts:
        resolved = shortcuts[parts[0].lower()]
        parts = resolved.split()

    if len(parts) == 5:
        fields = ["minute", "hour", "day of month", "month", "day of week"]
    elif len(parts) == 6:
        fields = ["second", "minute", "hour", "day of month", "month", "day of week"]
    elif len(parts) == 7:
        fields = ["second", "minute", "hour", "day of month", "month", "day of week", "year"]
    else:
        return f"Error: Expected 5-7 fields, got {len(parts)}. Format: MIN HOUR DOM MON DOW"

    dow_names = {"0": "Sunday", "1": "Monday", "2": "Tuesday", "3": "Wednesday",
                 "4": "Thursday", "5": "Friday", "6": "Saturday", "7": "Sunday",
                 "SUN": "Sunday", "MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday",
                 "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday"}
    month_names = {"1": "January", "2": "February", "3": "March", "4": "April",
                   "5": "May", "6": "June", "7": "July", "8": "August",
                   "9": "September", "10": "October", "11": "November", "12": "December",
                   "JAN": "January", "FEB": "February", "MAR": "March", "APR": "April",
                   "MAY": "May", "JUN": "June", "JUL": "July", "AUG": "August",
                   "SEP": "September", "OCT": "October", "NOV": "November", "DEC": "December"}

    explanations = []
    for i, (part, field) in enumerate(zip(parts, fields)):
        explanations.append(f"  {field:<15} {part:<12} → {_explain_field(part, field, dow_names, month_names)}")

    # Build human summary
    summary = _build_summary(parts, fields, dow_names, month_names)

    return f"Cron: {expression}\n\n{''.join(e + chr(10) for e in explanations)}\nSummary: {summary}"


# ---- Internals ----

def _parse_date(s: str):
    if not s or s.lower() in ("today", "now"):
        return date.today()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return f"Error: Cannot parse date '{s}'. Use YYYY-MM-DD format."


def _explain_field(part, field, dow_names, month_names):
    if part == "*":
        return f"every {field}"
    if part.startswith("*/"):
        return f"every {part[2:]} {field}s"
    if "-" in part and "/" not in part:
        tokens = part.split("-")
        if field == "day of week":
            tokens = [dow_names.get(t.upper(), t) for t in tokens]
        elif field == "month":
            tokens = [month_names.get(t.upper(), t) for t in tokens]
        return f"{tokens[0]} through {tokens[-1]}"
    if "," in part:
        tokens = part.split(",")
        if field == "day of week":
            tokens = [dow_names.get(t.upper(), t) for t in tokens]
        elif field == "month":
            tokens = [month_names.get(t.upper(), t) for t in tokens]
        return ", ".join(tokens)
    # Single value
    if field == "day of week":
        return dow_names.get(part.upper(), part)
    if field == "month":
        return month_names.get(part.upper(), part)
    return f"at {field} {part}"


def _build_summary(parts, fields, dow_names, month_names):
    # Simple 5-field cron
    idx = 0 if fields[0] == "minute" else 1  # offset for second field
    minute = parts[idx]
    hour = parts[idx + 1]
    dom = parts[idx + 2]
    month = parts[idx + 3]
    dow = parts[idx + 4]

    # Time part
    if minute.startswith("*/"):
        time_str = f"every {minute[2:]} minutes"
    elif hour == "*" and minute != "*":
        time_str = f"at minute {minute} of every hour"
    elif hour != "*" and minute != "*":
        time_str = f"at {hour.zfill(2)}:{minute.zfill(2)}"
    elif hour.startswith("*/"):
        time_str = f"every {hour[2:]} hours"
    else:
        time_str = "every minute"

    # Day restrictions
    restrictions = []
    if dow != "*":
        if "-" in dow:
            tokens = dow.upper().split("-")
            restrictions.append(f"{dow_names.get(tokens[0], tokens[0])} to {dow_names.get(tokens[1], tokens[1])}")
        else:
            days = [dow_names.get(d.upper(), d) for d in dow.split(",")]
            restrictions.append(", ".join(days))
    if dom != "*":
        restrictions.append(f"on day {dom} of the month")
    if month != "*":
        months = [month_names.get(m.upper(), m) for m in month.split(",")]
        restrictions.append(f"in {', '.join(months)}")

    if restrictions:
        return f"Runs {time_str}, {'; '.join(restrictions)}"
    return f"Runs {time_str}"
