"""Tests for the WebContextFeature plugin."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from feature_web_context.web_context_feature import WebContextFeature, _WEB_CACHE, _get_or_fetch_content


def _run_initialize(
    feature: WebContextFeature,
    native_messages: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    state: Dict[str, Any] = {"config": config, "request": {}}
    return feature.initialize_request(native_messages, state)


def test_web_context_completions_use_cached_urls_sorted_by_length(monkeypatch) -> None:
    feature = WebContextFeature()

    _WEB_CACHE.clear()
    # URLs in non-length order to verify sorting.
    _WEB_CACHE["https://example.com/long/path"] = {"raw_html": "", "formats": {}}
    _WEB_CACHE["https://example.com"] = {"raw_html": "", "formats": {}}
    _WEB_CACHE["https://example.com/a"] = {"raw_html": "", "formats": {}}

    config: Dict[str, Any] = {"web_context_enabled": True}

    items = feature.get_completions(config, "@web:https://example.c")
    displays = [item["display"] for item in items]

    # Ignore any self-entry ("@web:...") when checking ordering; focus on
    # cached URLs and their length-based ordering.
    url_displays = [d for d in displays if not d.startswith("@web:")]

    assert url_displays[:3] == [
        "https://example.com",
        "https://example.com/a",
        "https://example.com/long/path",
    ]

    # Replacement for the first cached URL suggestion should include the
    # @web: prefix.
    first_cached = next(it for it in items if it["display"] == "https://example.com")
    assert first_cached["replacement"].startswith("@web:https://example.com")


def test_web_context_base_schemes_suggested_when_no_cached_urls() -> None:
    feature = WebContextFeature()

    _WEB_CACHE.clear()
    config: Dict[str, Any] = {"web_context_enabled": True}

    items = feature.get_completions(config, "@web:")
    displays = {item["display"] for item in items}

    assert "http://" in displays
    assert "https://" in displays

    replacements = {item["replacement"] for item in items}
    assert "@web:http://" in replacements
    assert "@web:https://" in replacements


def test_web_context_per_request_fetch_cache_resets(monkeypatch) -> None:
    feature = WebContextFeature()

    calls: list[str] = []

    def _fake_get(url: str, cfg: Dict[str, Any]) -> str:  # type: ignore[override]
        calls.append(url)
        return f"CONTENT({url})"

    monkeypatch.setattr(
        "feature_web_context.web_context_feature._get_or_fetch_content", _fake_get, raising=True
    )

    native = [{"role": "user", "content": "@web:https://example.com @web:https://example.com"}]
    config: Dict[str, Any] = {"web_context_enabled": True}

    # First request: two markers for the same URL should trigger a single
    # fetch due to the per-request fetch_cache.
    _run_initialize(feature, native, config)
    assert calls == ["https://example.com"]

    # Second request: cache is reset, so the URL is fetched again.
    _run_initialize(feature, native, config)
    assert calls == ["https://example.com", "https://example.com"]


def test_web_context_completions_with_schemes_and_cached_url() -> None:
    feature = WebContextFeature()

    _WEB_CACHE.clear()
    _WEB_CACHE["https://iocharts.io"] = {"downloaded": "", "formats": {}}

    config: Dict[str, Any] = {"web_context_enabled": True}

    # 1) Just @web: -> only base schemes.
    items = feature.get_completions(config, "@web:")
    displays = [item["display"] for item in items]
    assert "http://" in displays
    assert "https://" in displays
    assert all("iocharts" not in d for d in displays)

    # 2) @web:h -> both schemes + cached URL.
    items = feature.get_completions(config, "@web:h")
    displays = [item["display"] for item in items]
    assert "http://" in displays
    assert "https://" in displays
    assert "https://iocharts.io" in displays

    # 3) @web:https -> https:// + cached URL, but no http://.
    items = feature.get_completions(config, "@web:https")
    displays = [item["display"] for item in items]
    assert "http://" not in displays
    assert "https://" in displays
    assert "https://iocharts.io" in displays

    # 4) @web:https://i -> only the cached URL remains (no self-entry
    # for partial host).
    items = feature.get_completions(config, "@web:https://i")
    displays = [item["display"] for item in items]
    assert "https://iocharts.io" in displays
    assert all(d != "@web:https://i" for d in displays)


def test_web_context_completion_includes_typed_full_url() -> None:
    feature = WebContextFeature()

    _WEB_CACHE.clear()
    config: Dict[str, Any] = {"web_context_enabled": True}

    text = "@web:https://iocharts.io"
    items = feature.get_completions(config, text)

    # Expect at least one completion that preserves the typed URL as a
    # clickable option (display is the bare URL, not the @web: marker).
    matches = [it for it in items if it.get("url") == "https://iocharts.io"]
    assert matches, f"expected a completion for {text!r} in {items!r}"
    comp = matches[0]
    assert comp["replacement"] == text
    assert comp["marker"] == text
    assert comp["url"] == "https://iocharts.io"


def test_initialize_request_expands_web_markers(monkeypatch) -> None:
    feature = WebContextFeature()

    # Avoid real network I/O by stubbing _get_or_fetch_content.
    def _fake_get(url: str, cfg: Dict[str, Any]) -> str:  # type: ignore[override]
        return f"CONTENT({url})"

    monkeypatch.setattr(
        "feature_web_context.web_context_feature._get_or_fetch_content", _fake_get, raising=True
    )

    native = [{"role": "user", "content": "Check this: @web:https://example.com"}]
    config: Dict[str, Any] = {"web_context_enabled": True}

    new_native, new_state = _run_initialize(feature, native, config)

    # Native messages should be expanded with fetched content only; the
    # template is applied at completion-accept time, not here.
    assert new_native != native
    body = new_native[0]["content"]
    assert "CONTENT(https://example.com)" in body


def test_initialize_request_expands_web_markers_with_space(monkeypatch) -> None:
    feature = WebContextFeature()

    def _fake_get(url: str, cfg: Dict[str, Any]) -> str:  # type: ignore[override]
        return f"CONTENT({url})"

    monkeypatch.setattr(
        "feature_web_context.web_context_feature._get_or_fetch_content", _fake_get, raising=True
    )

    native = [{"role": "user", "content": "Check this: @web: https://example.com"}]
    config: Dict[str, Any] = {"web_context_enabled": True}

    new_native, new_state = _run_initialize(feature, native, config)

    # Native messages should be expanded with fetched content only; the
    # template is applied at completion-accept time, not here.
    assert new_native != native
    body = new_native[0]["content"]
    assert "CONTENT(https://example.com)" in body


def test_web_context_custom_template(monkeypatch) -> None:
    feature = WebContextFeature()

    def _fake_get(url: str, cfg: Dict[str, Any]) -> str:  # type: ignore[override]
        return "BODY"

    monkeypatch.setattr(
        "feature_web_context.web_context_feature._get_or_fetch_content", _fake_get, raising=True
    )

    # Simulate an accepted completion: apply_completion should wrap the
    # @web: marker using the configured template, leaving the marker
    # itself in place for later expansion.
    config: Dict[str, Any] = {
        "web_context_enabled": True,
        "web_context_template": "URL={url}\nCONTENT={marker}",
    }

    completion = {
        "url": "https://example.com",
        "marker": "@web:https://example.com",
        "replacement": "@web:https://example.com",
    }

    snippet = feature.apply_completion(config, "@web:https://example.com", completion)

    assert snippet.startswith("URL=https://example.com")
    assert "CONTENT=@web:https://example.com" in snippet


def test_web_context_fetch_on_completion_uses_content(monkeypatch) -> None:
    feature = WebContextFeature()

    def _fake_get(url: str, cfg: Dict[str, Any]) -> str:  # type: ignore[override]
        return "BODY"

    monkeypatch.setattr(
        "feature_web_context.web_context_feature._get_or_fetch_content", _fake_get, raising=True
    )

    config: Dict[str, Any] = {
        "web_context_enabled": True,
        "web_context_fetch_on_completion": True,
        "web_context_template": "URL={url}\nCONTENT={content}",
    }

    completion = {
        "url": "https://example.com",
        "marker": "@web:https://example.com",
        "replacement": "@web:https://example.com",
    }

    snippet = feature.apply_completion(config, "@web:https://example.com", completion)

    assert snippet.startswith("URL=https://example.com")
    assert "CONTENT=BODY" in snippet
    # Marker should not appear when fetching on completion.
    assert "@web:https://example.com" not in snippet
