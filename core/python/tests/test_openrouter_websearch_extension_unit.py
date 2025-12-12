"""Unit tests for OpenRouter web search extension."""

from __future__ import annotations

from typing import Any, Dict, List

from plugins.openrouter_websearch_extension import OpenRouterWebSearchExtension


def _make_annotation(url: str, title: str | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"url": url}
    if title is not None:
        payload["title"] = title
    return {"type": "url_citation", "url_citation": payload}


def test_extension_name_and_version() -> None:
    ext = OpenRouterWebSearchExtension()
    assert ext.name == "openrouter_websearch"
    assert ext.version == "0.1.0"


def test_get_tags_and_required_tags() -> None:
    ext = OpenRouterWebSearchExtension()
    tags = ext.get_tags({}, [])
    assert "ext:openrouter_websearch" in tags

    required = ext.required_tags()
    assert "openrouter" in required


def test_init_enabled_by_default() -> None:
    ext = OpenRouterWebSearchExtension()
    config: Dict[str, Any] = {}
    state: Dict[str, Any] = {}

    new_state = ext.init(config, state)

    cfg = new_state.get("openrouter_websearch")
    assert cfg is not None
    assert cfg["enabled"] is True
    assert cfg["plugin_id"] == "web"
    assert cfg["engine"] == "native"


def test_init_can_be_disabled() -> None:
    ext = OpenRouterWebSearchExtension()
    config: Dict[str, Any] = {"enable_web_search": False}
    state: Dict[str, Any] = {}

    new_state = ext.init(config, state)

    assert new_state == state
    assert "openrouter_websearch" not in new_state


def test_initialize_request_injects_plugins_entry() -> None:
    ext = OpenRouterWebSearchExtension()
    config: Dict[str, Any] = {}
    base_state: Dict[str, Any] = {"config": config, "request": {"payload": {"model": "test"}}}

    state = ext.init(config, base_state)
    updated = ext.initialize_request([], state)

    payload = updated["request"]["payload"]
    assert payload["model"] == "test"
    plugins = payload.get("plugins")
    assert isinstance(plugins, list)
    assert {"id": "web", "engine": "native"} in plugins


def test_from_native_messages_extracts_citations() -> None:
    ext = OpenRouterWebSearchExtension()

    native: List[Dict[str, Any]] = [
        {
            "role": "assistant",
            "content": "Here is a link",
            "annotations": [
                _make_annotation("https://example.com", "Example"),
            ],
        }
    ]
    messages: List[Dict[str, Any]] = [
        {"role": "assistant", "content": "Here is a link", "metadata": {}},
    ]

    enhanced = ext.from_native_messages(native, messages)

    assert len(enhanced) == 1
    md = enhanced[0].get("metadata") or {}
    citations = md.get("url_citations")
    assert isinstance(citations, list)
    assert citations[0]["url"] == "https://example.com"
    assert citations[0]["title"] == "Example"


def test_process_delta_accumulates_citations() -> None:
    ext = OpenRouterWebSearchExtension()

    delta = {
        "message": {
            "role": "assistant",
            "content": "Here is a link",
            "annotations": [
                _make_annotation("https://example.com/1"),
                _make_annotation("https://example.com/2"),
            ],
        }
    }

    partial, acc = ext.process_delta(delta, None, {})
    assert partial is None
    citations = acc.get("url_citations")
    assert isinstance(citations, list)
    urls = {c["url"] for c in citations}
    assert "https://example.com/1" in urls
    assert "https://example.com/2" in urls

