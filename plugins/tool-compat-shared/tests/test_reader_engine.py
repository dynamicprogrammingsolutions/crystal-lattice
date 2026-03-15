from __future__ import annotations

from pathlib import Path

from tool_compat_shared.reader_engine import (
    build_qwen_truncation_wrapper,
    detect_bom,
    is_path_ignored,
    read_file_with_encoding,
)


def test_detect_bom_supports_utf16be_and_utf32le() -> None:
    assert detect_bom(b"\xfe\xffx") == ("utf16be", 2)
    assert detect_bom(b"\xff\xfe\x00\x00x") == ("utf32le", 4)


def test_read_file_with_encoding_handles_utf16be(tmp_path: Path) -> None:
    path = tmp_path / "utf16be.txt"
    path.write_bytes(b"\xfe\xff\x00H\x00i")
    assert read_file_with_encoding(path) == "Hi"


def test_is_path_ignored_reads_ignore_file(tmp_path: Path) -> None:
    (tmp_path / ".qwenignore").write_text("ignored/\n*.secret\n", encoding="utf-8")
    nested = tmp_path / "ignored" / "note.txt"
    nested.parent.mkdir(parents=True)
    nested.write_text("x", encoding="utf-8")
    secret = tmp_path / "token.secret"
    secret.write_text("x", encoding="utf-8")
    assert is_path_ignored(str(nested), root=str(tmp_path), ignore_filename=".qwenignore") is True
    assert is_path_ignored(str(secret), root=str(tmp_path), ignore_filename=".qwenignore") is True


def test_build_qwen_truncation_wrapper_is_stable() -> None:
    wrapped = build_qwen_truncation_wrapper("alpha", 2, 5, 10)
    assert wrapped == "Showing lines 2-5 of 10 total lines.\n\n---\n\nalpha"