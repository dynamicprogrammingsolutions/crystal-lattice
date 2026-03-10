from __future__ import annotations

from typing import Any, Dict

from openrouter_responses_plugins.openrouter_responses_reasoning_extension import (
    OpenRouterResponsesReasoningExtension,
)


def test_extension_metadata() -> None:
    ext = OpenRouterResponsesReasoningExtension()
    assert ext.name == "openrouter_responses_reasoning"
    assert ext.version == "0.1.0"


def test_tags_and_required_tags() -> None:
    ext = OpenRouterResponsesReasoningExtension()
    assert "ext:openrouter_responses_reasoning" in ext.get_tags({}, [])
    required = ext.required_tags()
    assert required == [
        "openrouter_responses",
        "supports_reasoning",
        "feature:request_options",
    ]


def test_init_is_noop_without_reasoning_config() -> None:
    ext = OpenRouterResponsesReasoningExtension()
    state: Dict[str, Any] = {"config": {}}
    out = ext.init({}, state)
    assert out == state


def test_init_and_initialize_request_populates_request_options() -> None:
    ext = OpenRouterResponsesReasoningExtension()
    config = {
        "enable_reasoning": True,
        "reasoning_effort": "low",
    }
    state: Dict[str, Any] = {"config": {}}
    state = ext.init(config, state)
    assert "openrouter_responses_reasoning" in state

    out = ext.initialize_request([], state)
    cfg = out.get("config") or {}
    request_options = cfg.get("request_options") or {}
    assert request_options.get("reasoning") == {"enabled": True, "effort": "low"}


def test_reasoning_summary_auto_is_injected_when_set() -> None:
    ext = OpenRouterResponsesReasoningExtension()
    config = {
        "enable_reasoning": True,
        "reasoning_effort": "low",
        "reasoning_summary": "auto",
    }
    state: Dict[str, Any] = {"config": {}}
    state = ext.init(config, state)
    out = ext.initialize_request([], state)
    cfg = out.get("config") or {}
    request_options = cfg.get("request_options") or {}
    assert request_options.get("reasoning") == {"enabled": True, "effort": "low", "summary": "auto"}
