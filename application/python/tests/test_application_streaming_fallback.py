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

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from tests.fake_image_generation_provider import FakeImageGenerationProvider  # noqa: E402


def _write_config(tmp_path: Path, *, provider_config: Dict[str, Any]) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "fake_image": {
                "provider": "fake_image_generation",
                "model": "fake-model",
                **provider_config,
            }
        },
        "plugins": [
            "tests.fake_image_generation_provider.FakeImageGenerationProvider",
            "tests.fake_image_generation_provider.FakeImageGenerationAttachmentsExtension",
        ],
        "agents": {"default": {"provider": "fake_image"}},
    }
    path = tmp_path / "config_fake_image_generation.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path, *, provider_config: Dict[str, Any]) -> AgentApplication:
    return AgentApplication(
        str(_write_config(tmp_path, provider_config=provider_config)),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )


def _send_one_request(app: AgentApplication, *, stream: bool) -> list[dict[str, Any]]:
    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session,
        "user",
        "Generate a fake image response.",
        {},
        base_config,
    )
    app.save_session(session)
    return list(app.send_request(core, session, base_config, stream=stream))


def test_application_retries_non_streaming_when_provider_streaming_not_implemented(
    tmp_path: Path,
) -> None:
    FakeImageGenerationProvider.reset_counts()
    app = _build_app(tmp_path, provider_config={})

    try:
        first_events = _send_one_request(app, stream=True)
        assert not [event for event in first_events if event.get("type") == "error"]
        assert [event for event in first_events if event.get("type") == "final"]
        assert FakeImageGenerationProvider.stream_api_calls == 1
        assert FakeImageGenerationProvider.call_api_calls == 1

        second_events = _send_one_request(app, stream=True)
        assert not [event for event in second_events if event.get("type") == "error"]
        assert [event for event in second_events if event.get("type") == "final"]
        assert FakeImageGenerationProvider.stream_api_calls == 1
        assert FakeImageGenerationProvider.call_api_calls == 2
    finally:
        app.close()


def test_application_config_stream_false_forces_non_streaming(tmp_path: Path) -> None:
    FakeImageGenerationProvider.reset_counts()
    app = _build_app(tmp_path, provider_config={"stream": False})

    try:
        events = _send_one_request(app, stream=True)
        started = [event for event in events if event.get("type") == "request_started"]
        assert started and started[-1]["stream"] is False
        assert not [event for event in events if event.get("type") == "error"]
        assert FakeImageGenerationProvider.stream_api_calls == 0
        assert FakeImageGenerationProvider.call_api_calls == 1
    finally:
        app.close()


def test_application_explicit_stream_false_overrides_config_stream_true(tmp_path: Path) -> None:
    FakeImageGenerationProvider.reset_counts()
    app = _build_app(tmp_path, provider_config={"stream": True})

    try:
        events = _send_one_request(app, stream=False)
        started = [event for event in events if event.get("type") == "request_started"]
        assert started and started[-1]["stream"] is False
        assert not [event for event in events if event.get("type") == "error"]
        assert FakeImageGenerationProvider.stream_api_calls == 0
        assert FakeImageGenerationProvider.call_api_calls == 1
    finally:
        app.close()