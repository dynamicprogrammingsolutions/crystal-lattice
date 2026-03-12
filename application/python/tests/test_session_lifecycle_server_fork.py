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
from agent_core import AgentCore  # noqa: E402

from tests.dummy_lifecycle_app_plugin import DummyLifecycleAppPlugin  # noqa: F401,E402
from tests.dummy_lifecycle_extension import DummyLifecycleExtension  # noqa: F401,E402
from tests.dummy_provider import DummyProvider  # noqa: F401,E402


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_lifecycle_extension.DummyLifecycleExtension",
            "tests.dummy_lifecycle_app_plugin.DummyLifecycleAppPlugin",
        ],
        "agents": {"default": {"provider": "dummy"}},
    }
    path = tmp_path / "config_server_lifecycle.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_server_fork_uses_application_lifecycle_path(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    config_path = _make_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        event_store=InMemoryEventStore(),
    )
    server_mod._agent_app = app

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "hello", config=base_config)
    app.save_session(session)

    resp = server_mod.fork_session(session.session_id, {"index": 0}, app_instance=app)

    forked = app.load_session_record(resp["session"]["session_id"])
    assert forked is not None
    assert forked.metadata["fork_source_session_id"] == session.session_id
    assert "session_fork" in forked.metadata["extension_lifecycle_log"]
