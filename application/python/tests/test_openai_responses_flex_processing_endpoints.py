from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
OPENAI_RESPONSES_SRC = ROOT / "plugins/openai_responses/src"
if str(OPENAI_RESPONSES_SRC) not in sys.path:
    sys.path.insert(0, str(OPENAI_RESPONSES_SRC))

from agent_app.application_future import AgentApplication  # noqa: E402
import pytest  # noqa: E402
from openai_responses_plugins.openai_responses_flex_processing_extension import (  # noqa: E402
    OpenAIResponsesFlexProcessingExtension,
)
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider  # noqa: E402


def _write_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai": {
                "provider": "openai_responses",
                "model": "gpt-5-mini",
                "api_key": "test_key",
                "base_url": "https://api.openai.com/v1",
                "timeout": 60,
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_flex_processing_extension.OpenAIResponsesFlexProcessingExtension",
        ],
        "agents": {"default": {"provider": "openai"}},
    }
    path = tmp_path / "config_openai_responses_flex_processing.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_openai_flex_processing_ui_schema_surfaces_session_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent_terminal_app import server as server_mod

    monkeypatch.setattr(OpenAIResponsesProvider, "get_models", lambda self, config: [])

    app = AgentApplication(
        str(_write_config(tmp_path)),
        str(tmp_path / "sessions"),
    )

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    schema_resp = server_mod.get_session_ui_schema(session_id, app_instance=app)
    flex_elements = [
        el for el in schema_resp["elements"] if el.get("plugin") == "openai_responses_flex_processing"
    ]

    keys = {el.get("key") for el in flex_elements if el.get("ui_type") == "config"}
    assert keys == {
        "enable_flex_processing",
        "flex_timeout_seconds",
        "enable_flex_retries",
        "flex_max_retries",
        "flex_stream_recovery_mode",
        "flex_stream_recovery_retries",
    }


def test_openai_flex_processing_defaults_stream_recovery_to_early_only() -> None:
    ext = OpenAIResponsesFlexProcessingExtension()

    state = ext.init({"enable_flex_processing": True}, {"request": {"payload": {}, "timeout": 60}})
    _native, updated_state = ext.initialize_request([], state)

    request = updated_state["request"]
    assert request["payload"]["service_tier"] == "flex"
    assert request["stream_recovery_mode"] == "early_only"
    assert request["stream_recovery_retries"] == 3