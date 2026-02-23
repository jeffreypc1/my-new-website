"""Tests for shared/usage_tracker.py — API usage tracking and cost estimation."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

import shared.usage_tracker as tracker_mod


@pytest.fixture(autouse=True)
def _isolate_tracker_files(tmp_path):
    """Redirect tracker file paths to tmp_path for every test."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    with patch.object(tracker_mod, "_CONFIG_DIR", config_dir), \
         patch.object(tracker_mod, "_USAGE_FILE", config_dir / "api-usage.json"), \
         patch.object(tracker_mod, "_BUDGETS_FILE", config_dir / "api-budgets.json"):
        yield


# ── Cost estimation ──────────────────────────────────────────────────────


class TestEstimateCost:
    def test_known_model_sonnet(self):
        # 1000 input, 500 output with sonnet pricing ($3/$15 per 1M)
        cost = tracker_mod.estimate_cost("claude-sonnet-4-5-20250929", 1000, 500)
        expected = (1000 * 3.00 + 500 * 15.00) / 1_000_000
        assert abs(cost - expected) < 1e-10

    def test_known_model_haiku(self):
        cost = tracker_mod.estimate_cost("claude-haiku-4-5-20251001", 1000, 500)
        expected = (1000 * 0.80 + 500 * 4.00) / 1_000_000
        assert abs(cost - expected) < 1e-10

    def test_unknown_model_falls_back_to_sonnet(self):
        cost = tracker_mod.estimate_cost("unknown-model", 1000, 500)
        sonnet_cost = tracker_mod.estimate_cost("claude-sonnet-4-5-20250929", 1000, 500)
        assert cost == sonnet_cost

    def test_zero_tokens(self):
        assert tracker_mod.estimate_cost("claude-sonnet-4-5-20250929", 0, 0) == 0.0


# ── Logging and loading entries ──────────────────────────────────────────


class TestLogAndLoadEntries:
    def test_log_creates_file(self):
        tracker_mod.log_api_call(
            service="anthropic",
            tool="brief-builder",
            operation="draft",
            model="claude-sonnet-4-5-20250929",
            input_tokens=100,
            output_tokens=50,
            estimated_cost_usd=0.001,
        )
        entries = tracker_mod._load_entries()
        assert len(entries) == 1
        assert entries[0]["service"] == "anthropic"
        assert entries[0]["tool"] == "brief-builder"
        assert entries[0]["input_tokens"] == 100

    def test_multiple_entries(self):
        for i in range(3):
            tracker_mod.log_api_call(
                service="anthropic", tool=f"tool-{i}", operation="draft"
            )
        assert len(tracker_mod._load_entries()) == 3

    def test_empty_file_returns_empty_list(self):
        assert tracker_mod._load_entries() == []

    def test_corrupt_file_returns_empty_list(self):
        tracker_mod._USAGE_FILE.write_text("NOT JSON")
        assert tracker_mod._load_entries() == []


# ── 90-day trim ──────────────────────────────────────────────────────────


class TestTrimOldEntries:
    def test_old_entries_are_trimmed(self):
        old_ts = (datetime.now() - timedelta(days=100)).isoformat(timespec="seconds")
        recent_ts = datetime.now().isoformat(timespec="seconds")

        entries = [
            {"timestamp": old_ts, "service": "anthropic", "tool": "old", "operation": "x"},
            {"timestamp": recent_ts, "service": "anthropic", "tool": "recent", "operation": "x"},
        ]
        tracker_mod._save_entries(entries)
        loaded = tracker_mod._load_entries()
        assert len(loaded) == 1
        assert loaded[0]["tool"] == "recent"


# ── Query helpers ────────────────────────────────────────────────────────


class TestGetEntriesSince:
    def test_filters_by_days(self):
        now = datetime.now()
        entries = [
            {"timestamp": (now - timedelta(days=5)).isoformat(), "service": "a", "tool": "t", "operation": "o"},
            {"timestamp": (now - timedelta(days=15)).isoformat(), "service": "a", "tool": "t", "operation": "o"},
            {"timestamp": (now - timedelta(days=40)).isoformat(), "service": "a", "tool": "t", "operation": "o"},
        ]
        tracker_mod._save_entries(entries)
        result = tracker_mod.get_entries_since(10)
        assert len(result) == 1

    def test_sorted_newest_first(self):
        now = datetime.now()
        entries = [
            {"timestamp": (now - timedelta(days=1)).isoformat(), "service": "a", "tool": "older", "operation": "o"},
            {"timestamp": now.isoformat(), "service": "a", "tool": "newer", "operation": "o"},
        ]
        tracker_mod._save_entries(entries)
        result = tracker_mod.get_entries_since(30)
        assert result[0]["tool"] == "newer"


class TestGetMonthEntries:
    def test_filters_current_month(self):
        now = datetime.now()
        this_month = now.isoformat(timespec="seconds")
        other_month = now.replace(month=1 if now.month != 1 else 12, year=now.year if now.month != 1 else now.year - 1).isoformat(timespec="seconds")

        entries = [
            {"timestamp": this_month, "service": "a", "tool": "t", "operation": "o"},
            {"timestamp": other_month, "service": "a", "tool": "t", "operation": "o"},
        ]
        tracker_mod._save_entries(entries)
        result = tracker_mod.get_month_entries()
        assert len(result) == 1


class TestGetMonthlySummary:
    def test_aggregates_by_service(self):
        now = datetime.now().isoformat(timespec="seconds")
        entries = [
            {"timestamp": now, "service": "anthropic", "tool": "t", "operation": "o",
             "input_tokens": 100, "output_tokens": 50, "estimated_cost_usd": 0.01},
            {"timestamp": now, "service": "anthropic", "tool": "t", "operation": "o",
             "input_tokens": 200, "output_tokens": 100, "estimated_cost_usd": 0.02},
            {"timestamp": now, "service": "google_translate", "tool": "t", "operation": "o",
             "input_tokens": 500, "estimated_cost_usd": 0.005},
        ]
        tracker_mod._save_entries(entries)
        summary = tracker_mod.get_monthly_summary()
        assert summary["anthropic"]["calls"] == 2
        assert summary["anthropic"]["input_tokens"] == 300
        assert summary["google_translate"]["calls"] == 1


class TestGetPerToolBreakdown:
    def test_groups_by_tool(self):
        now = datetime.now().isoformat(timespec="seconds")
        entries = [
            {"timestamp": now, "service": "anthropic", "tool": "brief-builder", "operation": "o",
             "input_tokens": 10, "output_tokens": 5, "estimated_cost_usd": 0.01},
            {"timestamp": now, "service": "anthropic", "tool": "brief-builder", "operation": "o",
             "input_tokens": 20, "output_tokens": 10, "estimated_cost_usd": 0.02},
            {"timestamp": now, "service": "anthropic", "tool": "cover-letters", "operation": "o",
             "input_tokens": 30, "output_tokens": 15, "estimated_cost_usd": 0.05},
        ]
        tracker_mod._save_entries(entries)
        breakdown = tracker_mod.get_per_tool_breakdown()
        tools = {r["tool"]: r for r in breakdown}
        assert tools["brief-builder"]["calls"] == 2
        assert tools["cover-letters"]["calls"] == 1
        # Sorted by cost descending
        assert breakdown[0]["tool"] == "cover-letters"


class TestGetDailyBreakdown:
    def test_per_day_totals(self):
        now = datetime.now()
        today = now.isoformat(timespec="seconds")
        yesterday = (now - timedelta(days=1)).isoformat(timespec="seconds")
        entries = [
            {"timestamp": today, "service": "a", "tool": "t", "operation": "o",
             "input_tokens": 10, "output_tokens": 5, "estimated_cost_usd": 0.01},
            {"timestamp": today, "service": "a", "tool": "t", "operation": "o",
             "input_tokens": 20, "output_tokens": 10, "estimated_cost_usd": 0.02},
            {"timestamp": yesterday, "service": "a", "tool": "t", "operation": "o",
             "input_tokens": 5, "output_tokens": 5, "estimated_cost_usd": 0.005},
        ]
        tracker_mod._save_entries(entries)
        breakdown = tracker_mod.get_daily_breakdown(7)
        assert len(breakdown) == 2
        # Sorted by date ascending
        assert breakdown[0]["date"] < breakdown[1]["date"]


# ── Budgets ──────────────────────────────────────────────────────────────


class TestBudgets:
    def test_default_budgets(self):
        budgets = tracker_mod.load_budgets()
        assert budgets["anthropic_monthly_usd"] == 50.0
        assert budgets["google_monthly_usd"] == 10.0

    def test_save_and_load(self):
        tracker_mod.save_budgets({"anthropic_monthly_usd": 100.0, "google_monthly_usd": 20.0})
        budgets = tracker_mod.load_budgets()
        assert budgets["anthropic_monthly_usd"] == 100.0

    def test_corrupt_file_returns_defaults(self):
        tracker_mod._BUDGETS_FILE.write_text("BAD")
        budgets = tracker_mod.load_budgets()
        assert "anthropic_monthly_usd" in budgets
