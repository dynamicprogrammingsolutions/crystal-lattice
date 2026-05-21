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


class _FakeUploadFileObject:
    def __init__(self, file_id: str) -> None:
        self.id = file_id

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return {"id": self.id}


class _FakeFilesResource:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FakeUploadFileObject:
        self.calls.append(kwargs)
        return _FakeUploadFileObject(f"file_{len(self.calls)}")


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
                "id": f"resp_{len(self.calls)}",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "ASSET_REF_OK"}],
                    }
                ],
            }
        )


class _FakeClient:
    def __init__(self) -> None:
        self.files = _FakeFilesResource()
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
                "attachment_upload_mode": "upload_before_send",
                "image_attachment_mode": "upload",
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_attachments_extension.OpenAIResponsesAttachmentsExtension",
        ],
        "agents": {"default": {"provider": "openai"}},
    }
    path = tmp_path / "config_openai_responses_asset_ref_send.json"
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

    app = AgentApplication(
        str(_write_config(tmp_path)),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    return app, fake_client


def test_application_send_request_uses_stored_session_asset_refs(
    tmp_path: Path, monkeypatch: Any
) -> None:
    app, fake_client = _build_app(tmp_path, monkeypatch)
    core, base_config, session = app.create_session("default")

    store_result = app.execute_session_action(
        "openai_responses_attachments",
        "store_attachment",
        {
            "session_id": session.session_id,
            "client_attachment_id": "draft_1",
            "attachment_type": "image",
            "filename": "square.png",
            "mime_type": "image/png",
            "data_base64": base64.b64encode(b"image-bytes").decode("ascii"),
        },
    )
    asset = store_result["attachment_asset"]

    loaded = app.load_session(session.session_id)
    assert loaded is not None
    core, base_config, session = loaded

    session = core.add_message(
        session,
        "user",
        "Use the stored attachment.",
        config=app.resolve_effective_config(base_config, session),
        context=app._build_core_handoff_context(base_config=base_config),
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "asset_ref": asset["asset_ref"],
                    "filename": asset["filename"],
                    "mime_type": asset["mime_type"],
                },
                "metadata": {},
            }
        ],
    )
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints
    final_session = checkpoints[-1]["session"]

    assert fake_client.files.calls
    assert fake_client.responses.calls[0]["input"][0]["content"] == [
        {"type": "input_text", "text": "Use the stored attachment."},
        {"type": "input_image", "file_id": "file_1"},
    ]

    stored_record = app.get_session_asset_store().load(
        session.session_id, asset["asset_ref"]["asset_id"]
    )
    assert stored_record.provider_refs["openai_responses"]["file_id"] == "file_1"

    final_session = core.add_message(
        final_session,
        "user",
        "Use the same attachment again.",
        config=app.resolve_effective_config(base_config, final_session),
        context=app._build_core_handoff_context(base_config=base_config),
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "asset_ref": asset["asset_ref"],
                    "filename": asset["filename"],
                    "mime_type": asset["mime_type"],
                },
                "metadata": {},
            }
        ],
    )
    app.save_session(final_session)

    second_events = list(
        app.send_request(core, final_session, base_config, stream=False)
    )
    second_checkpoints = [
        ev for ev in second_events if ev.get("type") == "session_checkpoint"
    ]
    assert second_checkpoints

    assert len(fake_client.files.calls) == 1
    assert fake_client.responses.calls[1]["input"][2]["content"] == [
        {"type": "input_text", "text": "Use the same attachment again."},
        {"type": "input_image", "file_id": "file_1"},
    ]


def test_modify_message_and_rebuild_native_history_keep_session_asset_context(
    tmp_path: Path, monkeypatch: Any
) -> None:
    app, fake_client = _build_app(tmp_path, monkeypatch)
    core, base_config, session = app.create_session("default")

    store_result = app.execute_session_action(
        "openai_responses_attachments",
        "store_attachment",
        {
            "session_id": session.session_id,
            "client_attachment_id": "draft_1",
            "attachment_type": "image",
            "filename": "square.png",
            "mime_type": "image/png",
            "data_base64": base64.b64encode(b"image-bytes").decode("ascii"),
        },
    )
    asset = store_result["attachment_asset"]

    loaded = app.load_session(session.session_id)
    assert loaded is not None
    core, base_config, session = loaded
    effective_config = app.resolve_effective_config(base_config, session)

    session = core.add_message(
        session,
        "user",
        "Use the stored attachment.",
        config=effective_config,
        context=app._build_core_handoff_context(base_config=base_config),
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "asset_ref": asset["asset_ref"],
                    "filename": asset["filename"],
                    "mime_type": asset["mime_type"],
                },
                "metadata": {},
            }
        ],
    )
    app.save_session(session)

    first_events = list(app.send_request(core, session, base_config, stream=False))
    first_checkpoints = [
        ev for ev in first_events if ev.get("type") == "session_checkpoint"
    ]
    assert first_checkpoints
    session = first_checkpoints[-1]["session"]

    session = core.modify_message(
        session,
        0,
        "Use the edited stored attachment.",
        app.resolve_effective_config(base_config, session),
        context=app._build_core_handoff_context(base_config=base_config),
    )
    assert isinstance((session.metadata or {}).get("native_messages"), list)
    app.save_session(session)

    second_events = list(app.send_request(core, session, base_config, stream=False))
    second_checkpoints = [
        ev for ev in second_events if ev.get("type") == "session_checkpoint"
    ]
    assert second_checkpoints
    assert len(fake_client.files.calls) == 1

    rebuilt = core.rebuild_native_history(
        session,
        app.resolve_effective_config(base_config, session),
        context=app._build_core_handoff_context(base_config=base_config),
    )
    assert isinstance((rebuilt.metadata or {}).get("native_messages"), list)
    app.save_session(rebuilt)

    third_events = list(app.send_request(core, rebuilt, base_config, stream=False))
    third_checkpoints = [
        ev for ev in third_events if ev.get("type") == "session_checkpoint"
    ]
    assert third_checkpoints
    assert len(fake_client.files.calls) == 1
