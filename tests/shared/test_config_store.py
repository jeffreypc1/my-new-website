"""Tests for shared/config_store.py — centralized config read/write."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import shared.config_store as config_mod


@pytest.fixture(autouse=True)
def _isolate_config_dir(tmp_path):
    """Redirect CONFIG_DIR to tmp_path for every test."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    with patch.object(config_mod, "CONFIG_DIR", config_dir):
        yield config_dir


# ── load_config ──────────────────────────────────────────────────────────


class TestLoadConfig:
    def test_returns_none_when_missing(self):
        assert config_mod.load_config("nonexistent") is None

    def test_reads_valid_json(self, _isolate_config_dir):
        path = _isolate_config_dir / "my-tool.json"
        path.write_text(json.dumps({"key": "value"}))
        result = config_mod.load_config("my-tool")
        assert result == {"key": "value"}

    def test_returns_none_on_corrupt_json(self, _isolate_config_dir):
        path = _isolate_config_dir / "bad.json"
        path.write_text("NOT VALID JSON")
        assert config_mod.load_config("bad") is None


# ── save_config ──────────────────────────────────────────────────────────


class TestSaveConfig:
    def test_creates_file(self, _isolate_config_dir):
        config_mod.save_config("new-tool", {"a": 1, "b": "two"})
        path = _isolate_config_dir / "new-tool.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data == {"a": 1, "b": "two"}

    def test_overwrites_existing(self, _isolate_config_dir):
        config_mod.save_config("tool", {"v": 1})
        config_mod.save_config("tool", {"v": 2})
        result = config_mod.load_config("tool")
        assert result["v"] == 2


# ── get_config_value ─────────────────────────────────────────────────────


class TestGetConfigValue:
    def test_returns_default_when_no_config(self):
        assert config_mod.get_config_value("missing", "key", "default") == "default"

    def test_returns_value_when_present(self, _isolate_config_dir):
        config_mod.save_config("tool", {"timeout": 30})
        assert config_mod.get_config_value("tool", "timeout", 10) == 30

    def test_returns_default_for_missing_key(self, _isolate_config_dir):
        config_mod.save_config("tool", {"timeout": 30})
        assert config_mod.get_config_value("tool", "retries", 3) == 3


# ── is_component_enabled ─────────────────────────────────────────────────


class TestIsComponentEnabled:
    def test_default_when_no_global_settings(self):
        assert config_mod.is_component_enabled("feedback", "brief-builder") is True
        assert config_mod.is_component_enabled("feedback", "brief-builder", default=False) is False

    def test_reads_from_global_settings(self, _isolate_config_dir):
        config_mod.save_config("global-settings", {
            "component_toggles": {
                "feedback": {
                    "brief-builder": False,
                    "cover-letters": True,
                }
            }
        })
        assert config_mod.is_component_enabled("feedback", "brief-builder") is False
        assert config_mod.is_component_enabled("feedback", "cover-letters") is True

    def test_missing_component_returns_default(self, _isolate_config_dir):
        config_mod.save_config("global-settings", {"component_toggles": {}})
        assert config_mod.is_component_enabled("unknown", "tool") is True

    def test_missing_tool_returns_default(self, _isolate_config_dir):
        config_mod.save_config("global-settings", {
            "component_toggles": {"feedback": {}}
        })
        assert config_mod.is_component_enabled("feedback", "missing-tool", default=False) is False
