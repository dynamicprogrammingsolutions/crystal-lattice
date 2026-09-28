"""Ordering tests for application-level UI schema elements.

Contract (mirrors the core): every UI element may carry an optional
numeric ``order``; the application layer stamps an effective order —
explicit value when set, else a default from the app-plugin band
(5000 + position * 10) — and returns the element list sorted by it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_app.application_future import AgentApplication
from agent_core import AgentCore

from .dummy_provider import DummyProvider  # noqa: F401


class FirstAppPlugin:
    name = "first_app_plugin"
    version = "1.0.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "session_action",
                "id": "first_action",
                "label": "First",
                "action_id": "first_action",
            },
            {
                "ui_type": "session_action",
                "id": "first_override",
                "label": "First override",
                "action_id": "first_action",
                "order": 4990,
            },
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": "first_action",
                "label": "First action",
                "inputs": {},
            }
        ]


class SecondAppPlugin:
    name = "second_app_plugin"
    version = "1.0.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "session_action",
                "id": "second_action",
                "label": "Second",
                "action_id": "second_action",
            },
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": "second_action",
                "label": "Second action",
                "inputs": {},
            }
        ]


def _make_config_with_app_plugins(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {"dummy": {"provider": "dummy_provider", "model": "test-model"}},
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.test_application_ui_schema_ordering.FirstAppPlugin",
            "tests.test_application_ui_schema_ordering.SecondAppPlugin",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
        "application": {},
    }
    path = tmp_path / "config_app_ui_ordering.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_app_plugin_defaults_and_explicit_override(tmp_path: Path) -> None:
    config_path = _make_config_with_app_plugins(tmp_path)
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore
    )

    elements = app.get_application_ui_schema()

    by_id = {el.get("id"): el for el in elements}
    assert by_id["first_action"].get("order") == 5010
    assert by_id["second_action"].get("order") == 5020
    assert by_id["first_override"].get("order") == 4990

    orders = [el.get("order") for el in elements]
    assert orders == sorted(orders)
    # The explicit 4990 override sorts before both plugin defaults.
    assert elements[0].get("id") == "first_override"


def test_session_application_ui_schema_is_ordered(tmp_path: Path) -> None:
    config_path = _make_config_with_app_plugins(tmp_path)
    app = AgentApplication(
        str(config_path), str(tmp_path / "sessions"), core_factory=AgentCore
    )

    _core, _base_config, session = app.create_session("default")
    elements = app.get_session_application_ui_schema(session.session_id)

    orders = [el.get("order") for el in elements]
    assert orders
    assert orders == sorted(orders)
    for order in orders:
        assert isinstance(order, (int, float))
        assert not isinstance(order, bool)
