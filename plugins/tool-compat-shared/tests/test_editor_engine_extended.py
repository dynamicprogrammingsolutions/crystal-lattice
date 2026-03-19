from __future__ import annotations

from pathlib import Path

from tool_compat_shared.editor_engine import write_text_file


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
