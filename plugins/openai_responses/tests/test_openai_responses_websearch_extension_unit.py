from __future__ import annotations

from typing import Any, Dict

from openai_responses_plugins.openai_responses_websearch_extension import (
    OpenAIResponsesWebSearchExtension,
)


def test_extension_name_tags_and_required_tags() -> None:
    ext = OpenAIResponsesWebSearchExtension()

    assert ext.name == "openai_responses_websearch"
    assert ext.version == "0.1.0"
    assert ext.priority == 110
    assert "ext:openai_responses_websearch" in ext.get_tags({}, [])
    assert ext.required_tags() == ["openai_responses"]


def test_init_disabled_by_default() -> None:
    ext = OpenAIResponsesWebSearchExtension()

    state = ext.init({}, {})

    assert state == {}


def test_ui_exposes_rich_web_search_toggle() -> None:
    element = OpenAIResponsesWebSearchExtension().get_ui_elements(
        tags=["ext:openai_responses_websearch"]
    )[0]

    assert element["key"] == "enable_web_search"
    assert element["icon"] == "globe"
    assert element["rich_ui"]["kind"] == "toggle"
    assert "icon" not in element["rich_ui"]
    assert element["rich_ui"]["options"][0]["tone"] == "primary"
    assert element["rich_ui"]["options"][1]["tone"] == "success"


def test_initialize_request_injects_web_search_tool_without_clobbering_tools() -> None:
    ext = OpenAIResponsesWebSearchExtension()
    config: Dict[str, Any] = {"enable_web_search": True}
    base_state: Dict[str, Any] = {
        "config": config,
        "request": {
            "payload": {
                "model": "gpt-5-mini",
                "tools": [{"type": "function", "name": "lookup"}],
            }
        },
    }

    state = ext.init(config, base_state)
    _native_messages, updated = ext.initialize_request([], state)

    payload = updated["request"]["payload"]
    assert payload["tools"] == [
        {"type": "function", "name": "lookup"},
        {"type": "web_search"},
    ]
    assert "include" not in payload


def test_initialize_request_adds_optional_fields_and_full_sources_include() -> None:
    ext = OpenAIResponsesWebSearchExtension()
    config: Dict[str, Any] = {
        "enable_web_search": True,
        "include_full_web_search_sources": True,
        "web_search_allowed_domains": ["https://Example.com/news", "sub.example.org"],
        "web_search_search_context_size": "high",
        "web_search_user_location_country": "US",
        "web_search_user_location_city": "New York",
        "web_search_user_location_timezone": "America/New_York",
    }
    base_state: Dict[str, Any] = {
        "config": config,
        "request": {
            "payload": {
                "model": "gpt-5-mini",
                "include": ["reasoning.encrypted_content"],
            }
        },
    }

    state = ext.init(config, base_state)
    _native_messages, updated = ext.initialize_request([], state)

    payload = updated["request"]["payload"]
    assert payload["include"] == [
        "reasoning.encrypted_content",
        "web_search_call.action.sources",
    ]
    assert payload["tools"] == [
        {
            "type": "web_search",
            "filters": {"allowed_domains": ["example.com", "sub.example.org"]},
            "search_context_size": "high",
            "user_location": {
                "type": "approximate",
                "country": "US",
                "city": "New York",
                "timezone": "America/New_York",
            },
        }
    ]


def test_initialize_request_avoids_duplicate_web_search_tool_and_include() -> None:
    ext = OpenAIResponsesWebSearchExtension()
    config: Dict[str, Any] = {
        "enable_web_search": True,
        "include_full_web_search_sources": True,
    }
    base_state: Dict[str, Any] = {
        "config": config,
        "request": {
            "payload": {
                "model": "gpt-5-mini",
                "tools": [{"type": "web_search"}],
                "include": ["web_search_call.action.sources"],
            }
        },
    }

    state = ext.init(config, base_state)
    _native_messages, updated = ext.initialize_request([], state)

    payload = updated["request"]["payload"]
    assert payload["tools"] == [{"type": "web_search"}]
    assert payload["include"] == ["web_search_call.action.sources"]


def test_initialize_request_accepts_existing_versioned_web_search_tool() -> None:
    ext = OpenAIResponsesWebSearchExtension()
    config: Dict[str, Any] = {"enable_web_search": True}
    base_state: Dict[str, Any] = {
        "config": config,
        "request": {
            "payload": {
                "model": "gpt-5-mini",
                "tools": [{"type": "web_search_2025_08_26"}],
            }
        },
    }

    state = ext.init(config, base_state)
    _native_messages, updated = ext.initialize_request([], state)

    payload = updated["request"]["payload"]
    assert payload["tools"] == [{"type": "web_search_2025_08_26"}]
