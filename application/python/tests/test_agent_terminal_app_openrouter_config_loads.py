from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))


def test_openrouter_config_loads_and_plugins_resolve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Load the OpenRouter terminal config and ensure plugin specs resolve.

    This test is intentionally offline: it does not call OpenRouter.
    It validates that the new plugin-repo architecture can be resolved
    via LocalPath module-only specs.
    """

    from agent_app.application_future import AgentApplication

    config_path = APP_PY / "agent_terminal_app" / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    # Ensure placeholders used by the config resolve.
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")

    # Ensure the default cache path (~/.crystal/cache/plugins) resolves into
    # a temporary home directory so the test is reproducible and does not
    # write into the developer's real home.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    app = AgentApplication(str(config_path), str(session_root))
    errs = app.get_config_errors()
    assert errs == [], f"expected no config/plugin errors, got: {errs}"
