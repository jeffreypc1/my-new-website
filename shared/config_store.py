"""Centralized configuration store for all office tools.

Reads and writes per-tool JSON config files in data/config/.
Each tool gets a single JSON file keyed by tool name (e.g., "case-checklist.json").
Tools load config values with fallback to their hardcoded defaults.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"


def load_config(tool_name: str) -> dict | None:
    """Load a tool's JSON config. Returns None if file doesn't exist."""
    path = CONFIG_DIR / f"{tool_name}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def save_config(tool_name: str, config: dict) -> None:
    """Write a tool's config to JSON. Creates dir if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = CONFIG_DIR / f"{tool_name}.json"
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False))


def get_config_value(tool_name: str, key: str, default: Any) -> Any:
    """Get a single key from a tool's config, with fallback to default."""
    config = load_config(tool_name)
    if config is None:
        return default
    return config.get(key, default)


def set_config_value(tool_name: str, key: str, value: Any) -> None:
    """Set a single key in a tool's config, preserving other keys."""
    config = load_config(tool_name) or {}
    config[key] = value
    save_config(tool_name, config)


def is_component_enabled(component_name: str, tool_name: str, default: bool = True) -> bool:
    """Check whether *component_name* is enabled for *tool_name*.

    Reads ``global-settings.json`` → ``component_toggles`` → *component_name*
    → *tool_name*.  Returns *default* when no config exists.
    """
    gs = load_config("global-settings")
    if not gs:
        return default
    toggles = gs.get("component_toggles", {})
    component = toggles.get(component_name, {})
    return component.get(tool_name, default)
