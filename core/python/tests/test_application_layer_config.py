"""Config resolution tests for the application layer."""

from __future__ import annotations

import os
from pathlib import Path

from agent_app.config import (
    load_raw_config,
    resolve_placeholders,
    build_agent_config,
)


def test_resolve_placeholders_collects_errors(tmp_path, monkeypatch):
    cfg = {
        "providers": {
            "openai": {
                "api_key": "${env:NON_EXISTENT}",
                "prompt": "${file:./no_such_file.txt}",
            }
        }
    }
    path = tmp_path / "config.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")

    raw = load_raw_config(path)
    resolved, errors = resolve_placeholders(raw, env={})

    provider = resolved["providers"]["openai"]
    assert provider["api_key"] == ""
    assert provider["prompt"] == ""
    assert errors
    kinds = {e["type"] for e in errors}
    assert "env_missing" in kinds or "file_missing" in kinds


def test_build_agent_config_merges_provider_and_agent():
    resolved = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "base"}
        },
        "agents": {
            "default": {"provider": "dummy", "model": "override"}
        },
    }

    cfg = build_agent_config(resolved, "default")
    assert cfg["provider"] == "dummy_provider"
    assert cfg["model"] == "override"
