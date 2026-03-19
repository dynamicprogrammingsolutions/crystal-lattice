from __future__ import annotations

from pathlib import Path

from tool_compat_shared.editor_engine import apply_text_replacements, write_text_file


def test_apply_text_replacements_single_match() -> None:
    content, count = apply_text_replacements("hello world", "world", "earth")
    assert content == "hello earth"
    assert count == 1


def test_apply_text_replacements_replace_all() -> None:
    content, count = apply_text_replacements("aaa bbb aaa", "aaa", "ccc", replace_all=True)
    assert content == "ccc bbb ccc"
    assert count == 2


def test_apply_text_replacements_no_match() -> None:
    content, count = apply_text_replacements("hello world", "xyz", "abc")
    assert content == "hello world"
    assert count == 0


def test_apply_text_replacements_empty_old() -> None:
    content, count = apply_text_replacements("hello", "", "abc")
    assert content == "hello"
    assert count == 0


def test_apply_text_replacements_identical_old_new() -> None:
    content, count = apply_text_replacements("hello", "hello", "hello")
    assert content == "hello"
    assert count == 0


def test_apply_text_replacements_multiline() -> None:
    content, count = apply_text_replacements("line1\nline2\nline1", "line1", "first")
    assert content == "first\nline2\nline1"
    assert count == 1


def test_apply_text_replacements_multiline_replace_all() -> None:
    content, count = apply_text_replacements("line1\nline2\nline1", "line1", "first", replace_all=True)
    assert content == "first\nline2\nfirst"
    assert count == 2


def test_write_text_file_append_mode(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("initial\n", encoding="utf-8")
    outcome = write_text_file(f, "appended\n", mode="append")
    assert outcome["ok"] is True
    assert outcome["code"] == "appended"
    assert outcome["file_existed"] is True
    assert f.read_text(encoding="utf-8") == "initial\nappended\n"


def test_write_text_file_append_creates_new_file(tmp_path: Path) -> None:
    f = tmp_path / "new.txt"
    outcome = write_text_file(f, "content\n", mode="append")
    assert outcome["ok"] is True
    # Append to non-existent file behaves like overwrite
    assert f.read_text(encoding="utf-8") == "content\n"


def test_write_text_file_overwrite_mode_still_default(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("old\n", encoding="utf-8")
    outcome = write_text_file(f, "new\n", mode="overwrite")
    assert outcome["ok"] is True
    assert outcome["code"] == "written"
    assert f.read_text(encoding="utf-8") == "new\n"
