"""Math tools — safe expression evaluation, unit conversion, base conversion."""

from __future__ import annotations

import ast
import math
import operator

# ---- Safe math evaluator ----

_SAFE_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCS = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sqrt": math.sqrt, "log": math.log, "log2": math.log2, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "ceil": math.ceil, "floor": math.floor, "factorial": math.factorial,
    "pi": math.pi, "e": math.e, "tau": math.tau,
    "degrees": math.degrees, "radians": math.radians,
    "gcd": math.gcd, "pow": pow,
}


def evaluate_expr(expression: str) -> str:
    """Safely evaluate a math expression (no exec/eval, AST-based).

    Args:
        expression: Math expression like '2**10 + sqrt(144) / 3'.
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval_node(tree.body)
        # Format nicely
        if isinstance(result, float):
            if result == int(result) and abs(result) < 1e15:
                return str(int(result))
            return f"{result:.10g}"
        return str(result)
    except (ValueError, TypeError, ZeroDivisionError) as e:
        return f"Math error: {e}"
    except Exception:
        return "Error: Invalid expression. Use numbers, operators (+−*/%), and functions (sqrt, log, sin, cos, abs, round, min, max)."


def convert_units(value: str, from_unit: str, to_unit: str) -> str:
    """Convert between common units.

    Args:
        value: Numeric value to convert.
        from_unit: Source unit (e.g., 'km', 'lb', 'C', 'GB').
        to_unit: Target unit (e.g., 'mi', 'kg', 'F', 'MB').
    """
    try:
        val = float(value)
    except ValueError:
        return f"Error: '{value}' is not a number."

    f = from_unit.strip().lower()
    t = to_unit.strip().lower()
    key = (f, t)

    # Temperature (special cases)
    if key == ("c", "f"):
        return f"{val}°C = {val * 9/5 + 32:.4g}°F"
    if key == ("f", "c"):
        return f"{val}°F = {(val - 32) * 5/9:.4g}°C"
    if key == ("c", "k"):
        return f"{val}°C = {val + 273.15:.4g} K"
    if key == ("k", "c"):
        return f"{val} K = {val - 273.15:.4g}°C"
    if key == ("f", "k"):
        return f"{val}°F = {(val - 32) * 5/9 + 273.15:.4g} K"
    if key == ("k", "f"):
        return f"{val} K = {(val - 273.15) * 9/5 + 32:.4g}°F"

    # All other conversions through a base unit per category
    result = _convert_via_base(val, f, t)
    if result is not None:
        return f"{val} {from_unit} = {result:.6g} {to_unit}"

    return f"Error: Unknown conversion {from_unit} → {to_unit}. Supported: length (m/km/mi/ft/in/cm/mm/yd), weight (kg/lb/oz/g/mg/ton/st), data (b/kb/mb/gb/tb/pb), time (s/ms/min/h/d/wk), volume (l/ml/gal/qt/pt/cup/floz)."


def number_base(number: str, from_base: str = "10", to_base: str = "16") -> str:
    """Convert a number between bases (2, 8, 10, 16, or any 2-36).

    Args:
        number: The number as a string (e.g., '255', '0xFF', '0b1010').
        from_base: Source base (2-36, or 'bin'/'oct'/'dec'/'hex').
        to_base: Target base (2-36, or 'bin'/'oct'/'dec'/'hex').
    """
    base_names = {"bin": 2, "oct": 8, "dec": 10, "hex": 16}
    try:
        fb = base_names.get(from_base.strip().lower(), int(from_base))
        tb = base_names.get(to_base.strip().lower(), int(to_base))
    except ValueError:
        return "Error: Bases must be integers 2-36 or bin/oct/dec/hex."

    if not (2 <= fb <= 36 and 2 <= tb <= 36):
        return "Error: Bases must be between 2 and 36."

    num_str = number.strip()
    # Auto-detect prefixed numbers
    try:
        if num_str.startswith(("0x", "0X")) and fb == 16:
            val = int(num_str, 16)
        elif num_str.startswith(("0b", "0B")) and fb == 2:
            val = int(num_str, 2)
        elif num_str.startswith(("0o", "0O")) and fb == 8:
            val = int(num_str, 8)
        else:
            val = int(num_str, fb)
    except ValueError:
        return f"Error: '{number}' is not valid in base {fb}."

    # Convert to target base
    if tb == 10:
        result = str(val)
    elif tb == 16:
        result = hex(val)
    elif tb == 8:
        result = oct(val)
    elif tb == 2:
        result = bin(val)
    else:
        result = _int_to_base(val, tb)

    return f"{number} (base {fb}) = {result} (base {tb})"


# ---- Internals ----

def _eval_node(node):
    """Recursively evaluate an AST node (safe subset)."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")
    if isinstance(node, ast.BinOp):
        op = _SAFE_OPS.get(type(node.op))
        if not op:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        # Cap power to prevent huge numbers
        if isinstance(node.op, ast.Pow) and isinstance(right, (int, float)) and right > 1000:
            raise ValueError("Exponent too large (max 1000)")
        return op(left, right)
    if isinstance(node, ast.UnaryOp):
        op = _SAFE_OPS.get(type(node.op))
        if not op:
            raise ValueError(f"Unsupported unary op: {type(node.op).__name__}")
        return op(_eval_node(node.operand))
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
            func = _SAFE_FUNCS[node.func.id]
            args = [_eval_node(a) for a in node.args]
            return func(*args)
        raise ValueError(f"Unsupported function")
    if isinstance(node, ast.Name):
        if node.id in _SAFE_FUNCS:
            val = _SAFE_FUNCS[node.id]
            if isinstance(val, (int, float)):
                return val
        raise ValueError(f"Unknown name: {node.id}")
    raise ValueError(f"Unsupported expression type: {type(node).__name__}")


# Unit conversion tables — value in base unit per 1 of named unit
_LENGTH = {"m": 1, "km": 1000, "mi": 1609.344, "ft": 0.3048, "in": 0.0254,
           "cm": 0.01, "mm": 0.001, "yd": 0.9144, "nm": 1852}
_WEIGHT = {"kg": 1, "g": 0.001, "mg": 0.000001, "lb": 0.453592, "oz": 0.0283495,
           "ton": 1000, "st": 6.35029}
_DATA = {"b": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**3, "tb": 1024**4, "pb": 1024**5}
_TIME = {"s": 1, "ms": 0.001, "us": 0.000001, "min": 60, "h": 3600, "d": 86400, "wk": 604800}
_VOLUME = {"l": 1, "ml": 0.001, "gal": 3.78541, "qt": 0.946353, "pt": 0.473176,
           "cup": 0.236588, "floz": 0.0295735}

_ALL_UNITS = [_LENGTH, _WEIGHT, _DATA, _TIME, _VOLUME]


def _convert_via_base(val, f, t):
    for table in _ALL_UNITS:
        if f in table and t in table:
            return val * table[f] / table[t]
    return None


def _int_to_base(num, base):
    if num == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    neg = num < 0
    num = abs(num)
    result = []
    while num:
        result.append(digits[num % base])
        num //= base
    if neg:
        result.append("-")
    return "".join(reversed(result))
