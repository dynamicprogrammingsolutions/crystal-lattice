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


def test_ui_elements_default_mode_shows_total_and_select() -> None:
    elements = _elements(None)

    # The config select is always contributed so the choice stays editable.
    select = elements[0]
    assert select["ui_type"] == "config"
    assert select["type"] == "select"
    assert select["key"] == "duration_breakdown"
    assert select["default"] == "none"
    assert [option["value"] for option in select["options"]] == [
        "none",
        "totals",
        "averages",
    ]

    assert _status_bar_paths(elements) == ["metadata.duration_session_total_formatted"]
    total = elements[1]
    assert total["template"] == "Total duration: {{data}}"
    assert total["condition"] == {
        "path": "metadata.duration_session_total_formatted",
        "exists": True,
    }


def test_ui_elements_show_toggle_gates_status_bar_only() -> None:
    elements = _elements({"show_duration_status_total": False})

    # The select stays editable even when the status bar is gated off.
    assert elements[0]["ui_type"] == "config"
    assert _status_bar_paths(elements) == []


def test_ui_elements_totals_mode_adds_requests() -> None:
    elements = _elements({"duration_breakdown": "totals"})

    assert _status_bar_paths(elements) == [
        "metadata.duration_session_total_formatted",
        "metadata.duration_session_requests_formatted",
        "metadata.tool_duration_session_total_formatted",
        "metadata.tool_duration_session_calls_formatted",
    ]
    requests_element = elements[2]
    assert requests_element["template"] == "requests: {{data}}"
    assert requests_element["condition"] == {
        "path": "metadata.duration_session_requests_formatted",
        "exists": True,
    }
    assert elements[3]["template"] == "tools: {{data}}"
    assert elements[4]["template"] == "tool calls: {{data}}"


def test_ui_elements_averages_mode_adds_averages_and_tools() -> None:
    elements = _elements({"duration_breakdown": "averages"})

    assert _status_bar_paths(elements) == [
        "metadata.duration_session_total_formatted",
        "metadata.duration_session_requests_formatted",
        "metadata.duration_session_average_formatted",
        "metadata.tool_duration_session_total_formatted",
        "metadata.tool_duration_session_calls_formatted",
        "metadata.tool_duration_session_average_formatted",
    ]
    assert elements[2]["template"] == "requests: {{data}}"
    assert elements[3]["template"] == "average: {{data}}"
    assert elements[4]["template"] == "tools: {{data}}"
    assert elements[5]["template"] == "tool calls: {{data}}"
    assert elements[6]["template"] == "tool average: {{data}}"


def test_ui_elements_invalid_mode_falls_back_to_none() -> None:
    elements = _elements({"duration_breakdown": "bogus"})

    assert _status_bar_paths(elements) == ["metadata.duration_session_total_formatted"]
    assert elements[0]["default"] == "none"
