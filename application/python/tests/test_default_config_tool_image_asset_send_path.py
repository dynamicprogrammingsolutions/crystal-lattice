from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any

import pytest
import requests


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core.tool_result_payloads import (  # noqa: E402
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    make_provider_native_tool_result,
)


CONFIG_PATH = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "config.json"
)
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB"
    "/6X7bAAAAABJRU5ErkJggg=="
)


def _set_default_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFIG_DIR", str(CONFIG_PATH.parent.resolve()))
    monkeypatch.setenv("BUILTIN_PLUGINS", str((ROOT / "plugins").resolve()))
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT",
        str(ROOT / "build" / "test-cloud-runtime-context"),
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-fireworks-key")
    monkeypatch.setenv("ZAI_API_KEY", "test-zai-key")
    monkeypatch.setenv("CLOUD_ORCHESTRATOR_URL", "http://cloud-orchestrator.test")
    monkeypatch.setenv("CLOUD_ORCHESTRATOR_TOKEN", "test-cloud-token")


def test_default_config_openrouter_expands_tool_asset_refs_after_system_message_rewrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_default_config_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("WORKING_DIR", str(tmp_path))

    captured_payloads: list[dict[str, Any]] = []

    class Response:
        ok = True
        status_code = 200
        reason = "OK"
        encoding = "utf-8"
        text = ""

        def iter_lines(self, decode_unicode: bool = True) -> list[str]:
            _ = decode_unicode
            return [
                'data: {"choices":[{"delta":{"role":"assistant","content":"done"}}]}',
                "data: [DONE]",
            ]

        def close(self) -> None:
            pass

    def post(self: requests.Session, *args: Any, **kwargs: Any) -> Response:
        _ = self, args
        payload = kwargs.get("json")
        assert isinstance(payload, dict)
        captured_payloads.append(payload)
        return Response()

    monkeypatch.setattr(requests.Session, "post", post)

    app = AgentApplication(
        str(CONFIG_PATH),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    assert app.get_config_errors() == []
    openrouter_provider = sys.modules.get("openrouter_plugins.openrouter_provider")
    assert openrouter_provider is not None
    monkeypatch.setattr(openrouter_provider.requests.Session, "post", post)

    core, base_config, session = app.create_session("kimi")
    record = app.get_session_asset_store().store_base64(
        session_id=session.session_id,
        attachment_type="image",
        filename="tiny.png",
        mime_type="image/png",
        data_base64=base64.b64encode(PNG_BYTES).decode("ascii"),
    )

    session = core.add_message(
        session,
        "user",
        "Continue after inspecting the image.",
        config=base_config,
    )
    tool_call = {
        "id": "functions.ReadMediaFile:0",
        "type": "function",
        "function": {
            "name": "ReadMediaFile",
            "arguments": json.dumps({"path": "tiny.png"}),
        },
    }
    session = core.add_message(
        session,
        "assistant",
        "",
        metadata={"tool_calls": [tool_call]},
        config=base_config,
    )
    tool_result = make_provider_native_tool_result(
        format=FORMAT_OPENAI_CHAT_COMPLETIONS,
        text="Loaded image file `tiny.png`.",
        content=[
            {"type": "text", "text": '<image path="tiny.png">'},
            {
                "type": "image_url",
                "image_url": {
                    "asset_ref": record.asset_ref(),
                    "filename": record.filename,
                    "mime_type": record.mime_type,
                },
            },
            {"type": "text", "text": "</image>"},
        ],
    )
    session = core.add_message(
        session,
        "tool",
        tool_result["text"],
        metadata={
            "tool_call_id": "functions.ReadMediaFile:0",
            "tool_name": "ReadMediaFile",
        },
        config=base_config,
        tool_result=tool_result,
    )
    session = app.save_session(session)

    events = list(app.send_request(core, session, base_config, stream=True))

    assert [event.get("type") for event in events if event.get("type") == "error"] == []
    assert captured_payloads
    payload_text = repr(captured_payloads[-1])
    assert "asset_ref" not in payload_text
    assert f"data:{record.mime_type};base64," in payload_text

    messages = captured_payloads[-1].get("messages")
    assert isinstance(messages, list)
    assert messages[0]["role"] == "system"
    assert "Kimi Code CLI" in messages[0]["content"]
    assert any(
        message.get("role") == "tool"
        and isinstance(message.get("content"), list)
        and any(
            isinstance(part, dict)
            and isinstance(part.get("image_url"), dict)
            and isinstance(part["image_url"].get("url"), str)
            and part["image_url"]["url"].startswith(f"data:{record.mime_type};base64,")
            for part in message["content"]
        )
        for message in messages
    )
