"""Number and cost formatting for the TUI."""

_SUFFIXES = ["", "K", "M", "B", "T", "Qa", "Qi", "Sx", "Sp", "Oc", "No", "Dc"]


def short_num(value: float, precision: int = 2) -> str:
    """Format a number with K/M/B suffixes."""
    if value is None:
        return "-"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if v == 0:
        return "0"
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v < 1000:
        if v == int(v):
            return f"{sign}{int(v)}"
        return f"{sign}{v:.{precision}f}".rstrip("0").rstrip(".")
    idx = 0
    while v >= 1000 and idx < len(_SUFFIXES) - 1:
        v /= 1000.0
        idx += 1
    return f"{sign}{v:.{precision}f}{_SUFFIXES[idx]}"


def format_rate(value: float) -> str:
    """Format a per-second rate, hiding when ~zero."""
    if value is None or abs(value) < 1e-6:
        return ""
    return f"+{short_num(value)}/s"


def format_cost(cost: dict, can_afford: bool = True) -> str:
    """Render a cost dict like '100 gold, 50 wood' (red if unaffordable)."""
    if not cost:
        return "-"
    parts = [f"{short_num(amount)} {res}" for res, amount in cost.items() if amount > 0]
    text = ", ".join(parts) if parts else "free"
    if not can_afford:
        return f"[red]{text}[/red]"
    return text


def format_seconds(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    if s < 86400:
        return f"{s // 3600}h {(s % 3600) // 60}m"
    return f"{s // 86400}d {(s % 86400) // 3600}h"
