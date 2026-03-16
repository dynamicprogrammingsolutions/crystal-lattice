from __future__ import annotations

from pathlib import Path

from tool_compat_shared.editor_engine import replace_literal_text, write_text_file


def test_write_text_file_creates_and_rejects_existing_create_only(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    created = write_text_file(target, "alpha\n", create_only=True)
    assert created["ok"] is True
    assert created["created"] is True
    assert target.read_text(encoding="utf-8") == "alpha\n"

    duplicate = write_text_file(target, "beta\n", create_only=True)
    assert duplicate["ok"] is False
    assert duplicate["code"] == "already_exists"


def test_replace_literal_text_handles_zero_one_and_many_matches(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("one\ntwo\none\n", encoding="utf-8")

    zero = replace_literal_text(target, "missing", "new")
    assert zero["ok"] is False
    assert zero["code"] == "no_occurrences"

    many = replace_literal_text(target, "one", "ONE")
    assert many["ok"] is False
    assert many["code"] == "multiple_occurrences"
    assert many["occurrences"] == 2

    all_matches = replace_literal_text(target, "one", "ONE", replace_all=True)
    assert all_matches["ok"] is True
    assert all_matches["occurrences"] == 2
    assert target.read_text(encoding="utf-8") == "ONE\ntwo\nONE\n"


def test_replace_literal_text_can_create_file_when_old_string_empty(tmp_path: Path) -> None:
    target = tmp_path / "created.txt"
    result = replace_literal_text(target, "", "hello\n", allow_missing_with_empty_old=True)
    assert result["ok"] is True
    assert result["created"] is True
    assert target.read_text(encoding="utf-8") == "hello\n"