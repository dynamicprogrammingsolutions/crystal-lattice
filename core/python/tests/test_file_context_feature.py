"""Tests for the FileContextFeature plugin."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from plugins.file_context_feature import FileContextFeature


def _run_initialize(
    feature: FileContextFeature,
    native_messages: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    state: Dict[str, Any] = {"config": config, "request": {}}
    return feature.initialize_request(native_messages, state)


def test_persistent_mode_without_residual_markers_updates_native_only() -> None:
    feature = FileContextFeature()

    # Avoid filesystem I/O by stubbing _read_file_range to return plain
    # content without any @file markers.
    def _fake_read(path: str, start: int, end: int, cfg: Dict[str, Any]) -> str:  # type: ignore[override]
        return "hello from file\n"

    feature._read_file_range = _fake_read  # type: ignore[assignment]

    native = [{"role": "user", "content": "before @file:foo.txt after"}]
    config = {"file_context_enabled": True, "file_context_on_the_fly": False}

    new_native, new_state = _run_initialize(feature, native, config)

    # Native messages should be expanded and no request['messages'] created.
    assert new_native != native
    assert new_native[0]["content"].startswith("before ")
    assert "@file:" not in new_native[0]["content"]
    request = new_state.get("request") or {}
    assert "messages" not in request


def test_persistent_mode_with_residual_markers_falls_back_to_on_the_fly() -> None:
    feature = FileContextFeature()

    # Stub _read_file_range so that the expanded content still contains an
    # @file: marker. This should trigger the guard and cause initialize_request
    # to fall back to on-the-fly behaviour.
    def _fake_read(path: str, start: int, end: int, cfg: Dict[str, Any]) -> str:  # type: ignore[override]
        return "@file:./.env\n"

    feature._read_file_range = _fake_read  # type: ignore[assignment]

    native = [{"role": "user", "content": "prefix @file:foo.txt"}]
    config = {"file_context_enabled": True, "file_context_on_the_fly": False}

    new_native, new_state = _run_initialize(feature, native, config)

    # Native messages should remain unchanged.
    assert new_native == native

    # A request['messages'] override should be present and expanded.
    request = new_state.get("request") or {}
    messages = request.get("messages")
    assert isinstance(messages, list) and messages
    assert messages[0]["content"] != native[0]["content"]
    # The expanded request content is allowed to contain @file:, since it is
    # request-local and will not be re-interpreted next turn.
