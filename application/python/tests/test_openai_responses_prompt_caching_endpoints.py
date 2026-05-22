from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

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
OPENAI_RESPONSES_SRC = ROOT / "plugins/openai_responses/src"
if str(OPENAI_RESPONSES_SRC) not in sys.path:
    sys.path.insert(0, str(OPENAI_RESPONSES_SRC))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
import openai_responses_plugins.openai_responses_provider as provider_module  # noqa: E402
from openai_responses_plugins.openai_responses_provider import (
    OpenAIResponsesProvider,
)  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.openai]


class _FakeResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return self._payload


class _FakeResponsesResource:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FakeResponse:
        self.calls.append(kwargs)
        return _FakeResponse(
            {
                "id": "resp_prompt_cache_test",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "PROMPT_CACHE_OK"}],
                    }
                ],
            }
        )


class _FakeClient:
    def __init__(self) -> None:
        self.responses = _FakeResponsesResource()


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
            "openai_responses_plugins.openai_responses_prompt_caching_extension.OpenAIResponsesPromptCachingExtension",
        ],
        "agents": {"default": {"provider": "openai"}},
    }
    path = tmp_path / "config_openai_responses_prompt_caching.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(
    tmp_path: Path, monkeypatch: Any
) -> tuple[AgentApplication, _FakeClient]:
    fake_client = _FakeClient()
    monkeypatch.setattr(provider_module, "OpenAI", lambda **kwargs: fake_client)
    monkeypatch.setattr(OpenAIResponsesProvider, "get_models", lambda self, config: [])
    monkeypatch.setattr(
        OpenAIResponsesProvider,
        "_create_sdk_client_with_options",
        lambda self, config, *, timeout, max_retries: fake_client,
    )

    config_path = _write_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    return app, fake_client


def test_openai_prompt_cache_ui_schema_and_create_time_key(
    tmp_path: Path, monkeypatch: Any
) -> None:
    from agent_terminal_app import server as server_mod

    app, _fake_client = _build_app(tmp_path, monkeypatch)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    loaded = app.load_session_record(session_id)
    assert loaded is not None
    overrides = (loaded.metadata or {}).get("overrides") or {}
    generated_key = overrides.get("prompt_cache_key")
    assert isinstance(generated_key, str)
    assert generated_key.startswith("opcache_")

    schema_resp = server_mod.get_session_ui_schema(session_id, app_instance=app)
    elements = schema_resp["elements"]
    prompt_elements = [
        el for el in elements if el.get("plugin") == "openai_responses_prompt_caching"
    ]
    keys = {el.get("key") for el in prompt_elements if el.get("ui_type") == "config"}
    assert keys == {
        "enable_prompt_cache_key",
        "prompt_cache_key",
        "enable_prompt_cache_retention_24h",
    }

    session_actions = [
        el for el in prompt_elements if el.get("ui_type") == "session_action"
    ]
    assert len(session_actions) == 1
    assert session_actions[0]["action_id"] == "regenerate_prompt_cache_key"
    assert session_actions[0]["action_owner"] == "provider_extension"


def test_openai_prompt_cache_key_can_be_edited_and_regenerated(
    tmp_path: Path, monkeypatch: Any
) -> None:
    from agent_terminal_app import server as server_mod

    app, _fake_client = _build_app(tmp_path, monkeypatch)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    server_mod.patch_session_overrides(
        session_id,
        {"key": "prompt_cache_key", "value": "manual-key"},
        app_instance=app,
    )
    overrides_resp = server_mod.get_session_overrides(session_id, app_instance=app)
    assert overrides_resp["overrides"]["prompt_cache_key"] == "manual-key"

    action_resp = server_mod.execute_action(
        {
            "plugin": "openai_responses_prompt_caching",
            "action_id": "regenerate_prompt_cache_key",
            "action_owner": "provider_extension",
            "inputs": {"session_id": session_id},
        },
        app_instance=app,
    )

    assert action_resp["status"] == "ok"
    loaded = app.load_session_record(session_id)
    assert loaded is not None
    regenerated_key = ((loaded.metadata or {}).get("overrides") or {}).get(
        "prompt_cache_key"
    )
    assert isinstance(regenerated_key, str)
    assert regenerated_key.startswith("opcache_")
    assert regenerated_key != "manual-key"


def test_openai_prompt_cache_request_prepare_repairs_legacy_sessions(
    tmp_path: Path, monkeypatch: Any
) -> None:
    app, fake_client = _build_app(tmp_path, monkeypatch)

    core, base_config, session = app.create_session("default")
    metadata = dict(session.metadata or {})
    overrides = dict((metadata.get("overrides") or {}))
    overrides.pop("prompt_cache_key", None)
    metadata["overrides"] = overrides
    legacy_session = type(session)(
        session_id=session.session_id,
        messages=session.messages,
        metadata=metadata,
    )
    app.save_session(legacy_session)

    loaded = app.load_session(legacy_session.session_id)
    assert loaded is not None
    core, base_config, loaded_session = loaded
    loaded_session = core.add_message(
        loaded_session, "user", "hello", config=base_config
    )
    app.save_session(loaded_session)

    events = list(app.send_request(core, loaded_session, base_config, stream=False))

    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints
    repaired_session = checkpoints[-1]["session"]
    repaired_key = ((repaired_session.metadata or {}).get("overrides") or {}).get(
        "prompt_cache_key"
    )
    assert isinstance(repaired_key, str)
    assert repaired_key.startswith("opcache_")

    assert fake_client.responses.calls
    request_payload = fake_client.responses.calls[-1]
    assert request_payload["prompt_cache_key"] == repaired_key


def test_openai_prompt_cache_fork_preserves_existing_key(
    tmp_path: Path, monkeypatch: Any
) -> None:
    app, _fake_client = _build_app(tmp_path, monkeypatch)

    core, base_config, session = app.create_session("default")
    original_key = ((session.metadata or {}).get("overrides") or {}).get(
        "prompt_cache_key"
    )
    assert isinstance(original_key, str)

    session = core.add_message(session, "user", "hello", config=base_config)
    app.save_session(session)

    _fork_core, _fork_base, forked = app.fork_session(
        core,
        session,
        base_config,
        upto_index=0,
        new_session_id="prompt-cache-fork",
    )

    forked_key = ((forked.metadata or {}).get("overrides") or {}).get(
        "prompt_cache_key"
    )
    assert forked_key == original_key


def test_openai_prompt_cache_request_prepare_rebuild_preserves_asset_context(
    tmp_path: Path, monkeypatch: Any
) -> None:
    app, fake_client = _build_app(tmp_path, monkeypatch)

    core, base_config, session = app.create_session("default")
    image_record = app.get_session_asset_store().store_base64(
        session_id=session.session_id,
        attachment_type="image",
        filename="square.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
    )

    native_messages = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hello"}],
        },
        {
            "type": "function_call_output",
            "call_id": "call_view_1",
            "output": [
                {"type": "input_text", "text": "<image>"},
                {
                    "type": "input_image",
                    "image_url": {
                        "asset_ref": image_record.asset_ref(),
                        "filename": image_record.filename,
                        "mime_type": image_record.mime_type,
                    },
                },
                {"type": "input_text", "text": "</image>"},
            ],
        },
    ]

    rebuilt_messages, rebuilt_native = core._rebuild_core_from_native(
        native_messages,
        base_config,
        context=app._context.build_core_handoff_context(base_config=base_config),
    )
    session = type(session)(
        session_id=session.session_id,
        messages=rebuilt_messages,
        metadata={
            **(session.metadata or {}),
            "native_messages": rebuilt_native,
            "native_messages_integrity": core._compute_native_integrity(
                rebuilt_messages
            ),
        },
    )
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints

    assert fake_client.responses.calls
    request_payload = fake_client.responses.calls[-1]
    assert request_payload["input"][1]["type"] == "function_call_output"
    expanded_image = request_payload["input"][1]["output"][1]
    assert expanded_image["type"] == "input_image"
    assert isinstance(expanded_image["image_url"], str)
    assert expanded_image["image_url"].startswith("data:image/png;base64,")
