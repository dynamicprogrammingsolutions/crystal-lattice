from __future__ import annotations

from typing import Any

import pytest

from plugins.request_options_feature import RequestOptionsFeature

from anthropic_plugins import AnthropicReasoningControlsExtension


def _official_capabilities(
    *,
    thinking_types: dict[str, bool],
    effort_levels: dict[str, bool],
) -> dict[str, Any]:
    return {
        "thinking": {
            "supported": True,
            "types": {
                key: {"supported": value} for key, value in thinking_types.items()
            },
        },
        "effort": {
            "supported": any(effort_levels.values()),
            **{key: {"supported": value} for key, value in effort_levels.items()},
        },
        "context_management": {
            "supported": True,
            "clear_thinking_20251015": {"supported": True},
            "clear_tool_uses_20250919": {"supported": True},
            "compact_20260112": {"supported": False},
        },
    }


def test_official_capabilities_are_normalized() -> None:
    extension = AnthropicReasoningControlsExtension()
    models = extension.get_models(
        {"model": "claude-sonnet-5"},
        [
            {
                "id": "claude-sonnet-5",
                "capabilities": _official_capabilities(
                    thinking_types={"enabled": False, "adaptive": True},
                    effort_levels={
                        "low": True,
                        "medium": True,
                        "high": True,
                        "xhigh": True,
                        "max": True,
                    },
                ),
            }
        ],
    )

    assert models[0]["anthropic_reasoning_controls"] == {
        "thinking_types": ["adaptive"],
        "effort_levels": ["low", "medium", "high", "xhigh", "max"],
        "adaptive_interleaving": True,
    }


@pytest.mark.parametrize(
    ("model", "thinking_types", "efforts"),
    [
        ("claude-haiku-4-5-20251001", ["enabled"], []),
        (
            "claude-opus-4-5-20251101",
            ["enabled"],
            ["low", "medium", "high"],
        ),
        (
            "claude-sonnet-4-6",
            ["enabled", "adaptive"],
            ["low", "medium", "high", "max"],
        ),
        (
            "claude-sonnet-5",
            ["adaptive"],
            ["low", "medium", "high", "xhigh", "max"],
        ),
        (
            "claude-opus-4-8",
            ["adaptive"],
            ["low", "medium", "high", "xhigh", "max"],
        ),
        (
            "claude-fable-5",
            ["adaptive"],
            ["low", "medium", "high", "xhigh", "max"],
        ),
        (
            "claude-mythos-preview",
            ["adaptive"],
            ["low", "medium", "high", "max"],
        ),
    ],
)
def test_known_model_regex_fallbacks(
    model: str,
    thinking_types: list[str],
    efforts: list[str],
) -> None:
    extension = AnthropicReasoningControlsExtension()

    models = extension.get_models({"model": model}, [{"id": model}])

    details = models[0]["anthropic_reasoning_controls"]
    assert details["thinking_types"] == thinking_types
    assert details.get("effort_levels", []) == efforts


def test_unknown_compatible_model_gets_no_invented_controls() -> None:
    extension = AnthropicReasoningControlsExtension()

    models = extension.get_models(
        {"model": "qwen3.5:0.8b"},
        [{"id": "qwen3.5:0.8b"}],
    )

    assert "anthropic_reasoning_controls" not in models[0]
    assert (
        extension.get_ui_elements(
            {"model": "qwen3.5:0.8b"},
            {"models": models},
        )
        == []
    )


def test_explicit_official_unsupported_descriptor_suppresses_regex_fallback() -> None:
    extension = AnthropicReasoningControlsExtension()

    models = extension.get_models(
        {"model": "claude-sonnet-5"},
        [
            {
                "id": "claude-sonnet-5",
                "capabilities": {
                    "thinking": {
                        "supported": False,
                        "types": {
                            "enabled": {"supported": False},
                            "adaptive": {"supported": False},
                        },
                    },
                    "effort": {
                        "supported": False,
                        "low": {"supported": False},
                        "high": {"supported": False},
                    },
                },
            }
        ],
    )

    assert "anthropic_reasoning_controls" not in models[0]


def test_explicit_capabilities_override_discovered_details() -> None:
    extension = AnthropicReasoningControlsExtension()
    config = {
        "model": "claude-sonnet-5",
        "anthropic_reasoning_capabilities": {
            "thinking_types": ["enabled"],
            "effort_levels": ["low", "high"],
            "adaptive_interleaving": False,
        },
    }

    models = extension.get_models(
        config,
        [
            {
                "id": "claude-sonnet-5",
                "capabilities": _official_capabilities(
                    thinking_types={"enabled": False, "adaptive": True},
                    effort_levels={
                        "low": True,
                        "medium": True,
                        "high": True,
                        "xhigh": True,
                        "max": True,
                    },
                ),
            }
        ],
    )

    details = models[0]["anthropic_reasoning_controls"]
    assert details["thinking_types"] == ["enabled"]
    assert details["effort_levels"] == ["low", "high"]
    assert details["adaptive_interleaving"] is False


def test_selected_missing_model_is_added_from_regex_fallback() -> None:
    extension = AnthropicReasoningControlsExtension()

    models = extension.get_models({"model": "claude-sonnet-4-6"}, [])

    assert models == [
        {
            "id": "claude-sonnet-4-6",
            "name": "claude-sonnet-4-6",
            "anthropic_reasoning_controls": {
                "thinking_types": ["enabled", "adaptive"],
                "effort_levels": ["low", "medium", "high", "max"],
                "adaptive_interleaving": True,
                "manual_interleaving_beta": "interleaved-thinking-2025-05-14",
            },
        }
    ]


def test_ui_uses_exact_selected_model_controls() -> None:
    extension = AnthropicReasoningControlsExtension()
    config = {
        "model": "claude-sonnet-4-6",
        "anthropic_reasoning_mode": "adaptive",
        "anthropic_reasoning_effort": "high",
        "anthropic_reasoning_display": "summarized",
        "anthropic_reasoning_budget_tokens": 2048,
    }
    models = extension.get_models(config, [{"id": "claude-sonnet-4-6"}])

    elements = extension.get_ui_elements(config, {"models": models})
    by_key = {element["key"]: element for element in elements}

    assert [
        option["value"] for option in by_key["anthropic_reasoning_mode"]["options"]
    ] == [
        "disabled",
        "manual",
        "adaptive",
    ]
    assert [
        option["value"] for option in by_key["anthropic_reasoning_effort"]["options"]
    ] == ["low", "medium", "high", "max"]
    assert by_key["anthropic_reasoning_effort"]["icon"] == "sliders"
    assert by_key["anthropic_reasoning_effort"]["rich_ui"] == {
        "kind": "dropdown",
        "label": "Reasoning effort",
        "show_label": False,
        "show_icon": False,
        "options": by_key["anthropic_reasoning_effort"]["options"],
        "placements": ["composer"],
        "default_pinned": True,
    }
    assert by_key["anthropic_reasoning_budget_tokens"]["default"] == 2048
    assert by_key["anthropic_reasoning_display"]["default"] == "summarized"


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (
            {"anthropic_reasoning_mode": "disabled"},
            {"thinking": {"type": "disabled"}},
        ),
        (
            {
                "anthropic_reasoning_mode": "manual",
                "anthropic_reasoning_budget_tokens": 2048,
                "anthropic_reasoning_display": "summarized",
                "anthropic_reasoning_effort": "high",
            },
            {
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 2048,
                    "display": "summarized",
                },
                "output_config": {"effort": "high"},
            },
        ),
        (
            {
                "anthropic_reasoning_mode": "adaptive",
                "anthropic_reasoning_display": "omitted",
                "anthropic_reasoning_effort": "max",
            },
            {
                "thinking": {"type": "adaptive", "display": "omitted"},
                "output_config": {"effort": "max"},
            },
        ),
    ],
)
def test_controls_map_to_anthropic_request_options(
    config: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    extension = AnthropicReasoningControlsExtension()
    state = {
        "config": config,
        "request": {"payload": {"model": "m", "messages": []}},
    }

    _messages, state = extension.initialize_request([], state)

    payload = state["request"]["payload"]
    for key, value in expected.items():
        assert payload[key] == value


def test_raw_request_options_override_controls_extension() -> None:
    extension = AnthropicReasoningControlsExtension()
    feature = RequestOptionsFeature()
    config = {
        "anthropic_reasoning_mode": "adaptive",
        "anthropic_reasoning_effort": "high",
        "request_options": {
            "thinking": {"type": "disabled"},
            "output_config": {"effort": "max"},
        },
    }
    state = {
        "config": config,
        "request": {"payload": {"model": "m", "messages": []}},
    }

    _messages, state = extension.initialize_request([], state)
    state = feature.init(config, state)
    _messages, state = feature.initialize_request([], state)

    assert state["request"]["payload"]["thinking"] == {"type": "disabled"}
    assert state["request"]["payload"]["output_config"] == {"effort": "max"}
