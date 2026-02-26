from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session


def test_system_message_feature_persists_single_template_system_message(tmp_path: Path) -> None:
    system_template = "You are a helpful system message for tests."
    config: Dict[str, Any] = {
        "providers": {
            "echo_with_system": {
                "provider": "echo_openai_like",
                "model": "echo-test-1",
                "timeout": 60,
                "system_message_enabled": True,
                "system_message": system_template,
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "feature_system_message.system_message_feature.SystemMessageFeature",
        ],
        "agents": {
            "default": {
                "provider": "echo_with_system",
            }
        },
    }

    cfg_path = tmp_path / "config_system_message_app.json"
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    session_root = tmp_path / "sessions"

    events_store = InMemoryEventStore()
    app = AgentApplication(str(cfg_path), str(session_root), event_store=events_store)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "first", metadata=None, config=base_config)

    events1 = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints1 = [ev for ev in events1 if ev.get("type") == "session_checkpoint"]
    assert checkpoints1
    session1 = checkpoints1[-1]["session"]
    assert isinstance(session1, Session)
    app.save_session(session1)

    native1 = session1.metadata.get("native_messages") or []
    sys_native1 = [m for m in native1 if isinstance(m, dict) and m.get("role") == "system"]
    assert sys_native1 and sys_native1[0].get("content") == system_template

    core2, base_config2, loaded1 = app.load_session(session1.session_id)
    session2 = core2.add_message(loaded1, "user", "second", metadata=None, config=base_config2)

    events2 = list(app.send_request(core2, session2, base_config2, overrides=None, stream=False))
    checkpoints2 = [ev for ev in events2 if ev.get("type") == "session_checkpoint"]
    assert checkpoints2
    session3 = checkpoints2[-1]["session"]
    assert isinstance(session3, Session)

    native2 = session3.metadata.get("native_messages") or []
    sys_native2 = [m for m in native2 if isinstance(m, dict) and m.get("role") == "system"]
    assert len(sys_native2) == 1
    assert sys_native2[0].get("content") == system_template
