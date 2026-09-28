from __future__ import annotations

import json
from pathlib import Path

from agent_app.application_future import AgentApplication
from agent_app.plugin_sources.dotted import DottedClassSource


def test_application_accepts_fixed_dotted_plugin_sources(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "plugin_policy": {
                    "allow_dynamic_plugin_install": False,
                    "allow_node_tools": False,
                    "allow_bash_tools": False,
                },
                "providers": {
                    "dummy": {
                        "provider": "dummy_provider",
                        "model": "test-model",
                    }
                },
                "plugins": ["tests.dummy_provider.DummyProvider"],
                "agents": {"default": {"provider": "dummy"}},
            }
        ),
        encoding="utf-8",
    )

    app = AgentApplication(
        config_path,
        tmp_path / "sessions",
        plugin_sources=[DottedClassSource()],
    )

    assert app.list_agents() == ["default"]
    _core, _base_config, session = app.create_session("default")
    assert app.load_session_record(session.session_id) is not None
