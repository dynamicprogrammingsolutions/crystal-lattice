"""Tests for the FileContextFeature plugin."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

from feature_file_context.file_context_feature import FileContextFeature


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


def test_apply_completion_builds_template_snippet() -> None:
    feature = FileContextFeature()

    config: Dict[str, Any] = {
        "file_context_enabled": True,
        "file_context_template": "{path}\n```{lang}\n@file:{path}:{range}\n```",
        "file_context_max_lines": 10,
        "working_directory": ".",
        "allowed_paths": ["."],
    }

    # Create a temporary file with a known number of lines.
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "bar.py")
        with open(path, "w", encoding="utf-8") as f:
            for i in range(1, 6):
                f.write(f"line {i}\n")

        config["working_directory"] = tmpdir

        completion = {
            "replacement": "@file:bar.py",
            "path": "bar.py",
            "range_input": "2",
        }

        text = "@file:bar.py:2"
        snippet = feature.apply_completion(config, text, completion)

        assert "bar.py" in snippet
        # With 5 lines in the file and start=2, default end should be 5.
        assert "@file:bar.py:2-5" in snippet


def test_get_completions_respects_gitignore(tmp_path) -> None:
    feature = FileContextFeature()
    try:
        from git import Repo  # type: ignore[import]
    except ModuleNotFoundError:
        pytest.skip("GitPython not installed")

    repo_dir = tmp_path
    (repo_dir / ".gitignore").write_text("ignored*.txt\n", encoding="utf-8")
    (repo_dir / "kept.txt").write_text("keep me", encoding="utf-8")
    (repo_dir / "ignored.txt").write_text("ignore me", encoding="utf-8")

    Repo.init(repo_dir)

    config: Dict[str, Any] = {
        "file_context_enabled": True,
        "working_directory": str(repo_dir),
        "allowed_paths": [str(repo_dir)],
    }

    # Use a string long enough to pass the len(text) >= 8 check
    text = "xx @file:"

    completions = feature.get_completions(config, text)
    paths = [c.get("path") for c in completions]

    assert "kept.txt" in paths
    assert "ignored.txt" in paths
    # Non-ignored files should be suggested before ignored ones.
    assert paths.index("kept.txt") < paths.index("ignored.txt")
