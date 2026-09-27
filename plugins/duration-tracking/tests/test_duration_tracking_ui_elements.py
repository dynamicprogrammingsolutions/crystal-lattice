"""Unit tests for the duration tracking status-bar UI elements."""

from __future__ import annotations

from typing import Any, Dict, List

from duration_tracking_plugins.duration_tracking_extension import (
    DurationTrackingExtension,
)


def _elements(config: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    return DurationTrackingExtension().get_ui_elements(config)


def _status_bar_paths(elements: List[Dict[str, Any]]) -> List[str]:
    return [
        element["data"]
        for element in elements
        if element.get("ui_type") == "status_bar"
    ]


def _footer_paths(elements: List[Dict[str, Any]]) -> List[str]:
    return [
        element["data"]
        for element in elements
        if element.get("ui_type") == "message_footer"
    ]


def _config_elements(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [element for element in elements if element.get("ui_type") == "config"]


def test_ui_elements_default_modes_are_clear_and_preserve_current_content() -> None:
    elements = _elements(None)

    configs = _config_elements(elements)
    assert [element["key"] for element in configs] == [
        "duration_primary",
        "duration_additional_fields",
        "duration_statistics",
    ]
    assert all(element["type"] == "select" for element in configs)
    assert [element["default"] for element in configs] == [
        "llm",
        "human",
        "none",
    ]

    assert _status_bar_paths(elements) == [
        "metadata.duration_session_total_formatted",
        "metadata.human_time_session_total_formatted",
    ]
    assert _footer_paths(elements) == ["metadata.human_time_turn_delta_formatted"]
    total = next(
        element
        for element in elements
        if element.get("data") == "metadata.duration_session_total_formatted"
    )
    assert total["template"] == "LLM duration: {{data}}"
    assert total["condition"] == {
        "path": "metadata.duration_session_total_formatted",
        "exists": True,
    }
    human = next(
        element
        for element in elements
        if element.get("data") == "metadata.human_time_session_total_formatted"
    )
    assert human["template"] == "Human time: {{data}}"
    footer = next(
        element
        for element in elements
        if element.get("data") == "metadata.human_time_turn_delta_formatted"
    )
    assert footer["template"] == "human time: {{data}}"
    assert footer["condition"] == {
        "all": [
            {
                "path": "metadata.human_time_turn_delta_formatted",
                "exists": True,
            },
            {"path": "role", "eq": "assistant"},
            {"path": "metadata.tool_calls", "empty": True},
        ]
    }


def test_ui_elements_all_options_render_independent_fields_and_statistics() -> None:
    elements = _elements(
        {
            "duration_primary": "llm_tools",
            "duration_additional_fields": "tools_human",
            "duration_statistics": "counts_averages",
        }
    )

    assert _status_bar_paths(elements) == [
        "metadata.duration_session_combined_total_formatted",
        "metadata.tool_duration_session_total_formatted",
        "metadata.human_time_session_total_formatted",
        "metadata.duration_session_requests_formatted",
        "metadata.duration_session_average_formatted",
        "metadata.tool_duration_session_calls_formatted",
        "metadata.tool_duration_session_average_formatted",
    ]
    templates = {
        element["data"]: element["template"]
        for element in elements
        if element.get("ui_type") == "status_bar"
    }
    assert (
        templates["metadata.duration_session_combined_total_formatted"]
        == "Duration: {{data}}"
    )
    assert (
        templates["metadata.tool_duration_session_total_formatted"]
        == "Tool duration: {{data}}"
    )
    assert templates["metadata.duration_session_requests_formatted"] == (
        "LLM calls: {{data}}"
    )
    assert templates["metadata.duration_session_average_formatted"] == (
        "LLM average: {{data}}"
    )
    assert templates["metadata.tool_duration_session_calls_formatted"] == (
        "Tool calls: {{data}}"
    )
    assert templates["metadata.tool_duration_session_average_formatted"] == (
        "Tool average: {{data}}"
    )


def test_hidden_primary_and_no_additional_fields_render_no_time_fields() -> None:
    elements = _elements(
        {
            "duration_primary": "hidden",
            "duration_additional_fields": "none",
            "duration_statistics": "counts_averages",
        }
    )

    assert _status_bar_paths(elements) == []
    assert _footer_paths(elements) == []


def test_combined_primary_includes_tool_statistics_without_separate_tool_total() -> (
    None
):
    elements = _elements(
        {
            "duration_primary": "llm_tools",
            "duration_additional_fields": "none",
            "duration_statistics": "counts",
        }
    )

    assert _status_bar_paths(elements) == [
        "metadata.duration_session_combined_total_formatted",
        "metadata.duration_session_requests_formatted",
        "metadata.tool_duration_session_calls_formatted",
    ]


def test_legacy_duration_breakdown_maps_to_new_choices() -> None:
    elements = _elements({"duration_breakdown": "averages"})

    configs = _config_elements(elements)
    assert [element["default"] for element in configs] == [
        "llm",
        "tools_human",
        "counts_averages",
    ]
    assert _status_bar_paths(elements) == [
        "metadata.duration_session_total_formatted",
        "metadata.tool_duration_session_total_formatted",
        "metadata.human_time_session_total_formatted",
        "metadata.duration_session_requests_formatted",
        "metadata.duration_session_average_formatted",
        "metadata.tool_duration_session_calls_formatted",
        "metadata.tool_duration_session_average_formatted",
    ]


def test_legacy_visibility_toggles_map_to_new_choices() -> None:
    elements = _elements(
        {
            "show_duration_status_total": False,
            "show_human_time_status_total": False,
            "duration_breakdown": "averages",
        }
    )

    assert [element["default"] for element in _config_elements(elements)] == [
        "hidden",
        "none",
        "none",
    ]
    assert _status_bar_paths(elements) == []
    assert _footer_paths(elements) == []


def test_invalid_new_modes_fall_back_to_legacy_defaults() -> None:
    elements = _elements(
        {
            "duration_primary": "bogus",
            "duration_additional_fields": "bogus",
            "duration_statistics": "bogus",
        }
    )

    assert [element["default"] for element in _config_elements(elements)] == [
        "llm",
        "human",
        "none",
    ]
