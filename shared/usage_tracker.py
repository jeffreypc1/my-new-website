"""API usage tracking for all office tool services.

Logs every API call (Anthropic, Google, etc.) with token counts and
estimated costs. Provides aggregation functions for the Admin Panel.

Data stored in data/config/api-usage.json (list of entries).
Budget settings in data/config/api-budgets.json.
Entries older than 90 days are trimmed on write.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
_USAGE_FILE = _CONFIG_DIR / "api-usage.json"
_BUDGETS_FILE = _CONFIG_DIR / "api-budgets.json"

# Pricing per million tokens (USD) — updated Feb 2026
PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
}

# Google Translate v2: $20 per 1M characters
GOOGLE_TRANSLATE_PRICE_PER_M_CHARS = 20.00


def _load_entries() -> list[dict]:
    if not _USAGE_FILE.exists():
        return []
    try:
        return json.loads(_USAGE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_entries(entries: list[dict]) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Trim entries older than 90 days
    cutoff = (datetime.now() - timedelta(days=90)).isoformat()
    entries = [e for e in entries if e.get("timestamp", "") >= cutoff]
    _USAGE_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False))


def load_budgets() -> dict:
    if not _BUDGETS_FILE.exists():
        return {"anthropic_monthly_usd": 50.0, "google_monthly_usd": 10.0}
    try:
        return json.loads(_BUDGETS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"anthropic_monthly_usd": 50.0, "google_monthly_usd": 10.0}


def save_budgets(budgets: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _BUDGETS_FILE.write_text(json.dumps(budgets, indent=2))


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for a Claude API call."""
    prices = PRICING.get(model, PRICING["claude-sonnet-4-5-20250929"])
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000


def log_api_call(
    service: str,
    tool: str,
    operation: str,
    *,
    model: str = "",
    input_tokens: int = 0,
    output_tokens: int = 0,
    estimated_cost_usd: float = 0.0,
    details: str = "",
) -> None:
    """Log a single API call."""
    entries = _load_entries()
    entries.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "service": service,
        "tool": tool,
        "operation": operation,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": round(estimated_cost_usd, 6),
        "details": details,
    })
    _save_entries(entries)


def get_entries_since(days: int = 30) -> list[dict]:
    """Return entries from the last N days, newest first."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    entries = _load_entries()
    return sorted(
        [e for e in entries if e.get("timestamp", "") >= cutoff],
        key=lambda e: e["timestamp"],
        reverse=True,
    )


def get_month_entries(year: int | None = None, month: int | None = None) -> list[dict]:
    """Return all entries for a given month (defaults to current month)."""
    now = datetime.now()
    y = year or now.year
    m = month or now.month
    prefix = f"{y}-{m:02d}"
    return [e for e in _load_entries() if e.get("timestamp", "").startswith(prefix)]


def get_monthly_summary() -> dict:
    """Aggregate current month's usage by service."""
    entries = get_month_entries()
    summary: dict = {
        "anthropic": {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0},
        "google_docs": {"calls": 0, "cost_usd": 0.0},
        "google_translate": {"calls": 0, "characters": 0, "cost_usd": 0.0},
    }
    for e in entries:
        svc = e.get("service", "")
        if svc == "anthropic":
            summary["anthropic"]["calls"] += 1
            summary["anthropic"]["input_tokens"] += e.get("input_tokens", 0)
            summary["anthropic"]["output_tokens"] += e.get("output_tokens", 0)
            summary["anthropic"]["cost_usd"] += e.get("estimated_cost_usd", 0.0)
        elif svc == "google_docs":
            summary["google_docs"]["calls"] += 1
        elif svc == "google_translate":
            summary["google_translate"]["calls"] += 1
            summary["google_translate"]["characters"] += e.get("input_tokens", 0)
            summary["google_translate"]["cost_usd"] += e.get("estimated_cost_usd", 0.0)
    return summary


def get_per_tool_breakdown() -> list[dict]:
    """Return current month's usage grouped by tool."""
    entries = get_month_entries()
    tools: dict[str, dict] = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost_usd": 0.0})
    for e in entries:
        tool = e.get("tool", "unknown")
        tools[tool]["calls"] += 1
        tools[tool]["tokens"] += e.get("input_tokens", 0) + e.get("output_tokens", 0)
        tools[tool]["cost_usd"] += e.get("estimated_cost_usd", 0.0)
    return [{"tool": k, **v} for k, v in sorted(tools.items(), key=lambda x: -x[1]["cost_usd"])]


def get_daily_breakdown(days: int = 30) -> list[dict]:
    """Return per-day totals for the last N days."""
    entries = get_entries_since(days)
    by_day: dict[str, dict] = defaultdict(lambda: {"calls": 0, "cost_usd": 0.0, "tokens": 0})
    for e in entries:
        day = e.get("timestamp", "")[:10]
        by_day[day]["calls"] += 1
        by_day[day]["cost_usd"] += e.get("estimated_cost_usd", 0.0)
        by_day[day]["tokens"] += e.get("input_tokens", 0) + e.get("output_tokens", 0)
    return [{"date": k, **v} for k, v in sorted(by_day.items())]
