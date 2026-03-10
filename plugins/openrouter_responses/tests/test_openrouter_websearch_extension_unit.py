"""Unit tests for OpenRouter /responses web search extension."""

from __future__ import annotations

from typing import Any, Dict

from openrouter_responses_plugins.openrouter_responses_websearch_extension import (
    OpenRouterResponsesWebSearchExtension,
)


def test_extension_name_and_version() -> None:
    ext = OpenRouterResponsesWebSearchExtension()
    assert ext.name == "openrouter_responses_websearch"
    assert ext.version == "0.1.0"


def test_get_tags_and_required_tags() -> None:
    ext = OpenRouterResponsesWebSearchExtension()
    tags = ext.get_tags({}, [])
    assert "ext:openrouter_responses_websearch" in tags

    required = ext.required_tags()
    assert "openrouter_responses" in required


def test_init_disabled_by_default() -> None:
    ext = OpenRouterResponsesWebSearchExtension()
    config: Dict[str, Any] = {}
    state: Dict[str, Any] = {}

    new_state = ext.init(config, state)

    # With no explicit config, web search should remain disabled.
    assert new_state == state
    assert "openrouter_responses_websearch" not in new_state


def test_init_can_be_enabled_explicitly() -> None:
    ext = OpenRouterResponsesWebSearchExtension()
    config: Dict[str, Any] = {"enable_web_search": True}
    state: Dict[str, Any] = {}

    new_state = ext.init(config, state)

    cfg = new_state.get("openrouter_responses_websearch")
    assert cfg is not None
    assert cfg["enabled"] is True
    assert cfg["plugin_id"] == "web"
    assert cfg["engine"] == "native"


def test_initialize_request_injects_plugins_entry() -> None:
    ext = OpenRouterResponsesWebSearchExtension()
    config: Dict[str, Any] = {"enable_web_search": True}
    base_state: Dict[str, Any] = {"config": config, "request": {"payload": {"model": "test"}}}

    state = ext.init(config, base_state)
    updated = ext.initialize_request([], state)

    payload = updated["request"]["payload"]
    assert payload["model"] == "test"
    plugins = payload.get("plugins")
    assert isinstance(plugins, list)
    assert {"id": "web", "engine": "native"} in plugins

