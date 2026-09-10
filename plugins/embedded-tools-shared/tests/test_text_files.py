from __future__ import annotations

from pathlib import Path

import pytest

from embedded_tools_shared import (
    DEFAULT_MAX_READ_BYTES,
    WorkspacePathError,
    edit_text_file,
    read_text_file,
    resolve_workspace_path,
    resolve_workspace_root,
    write_text_file,
)


def test_text_round_trip_and_line_window(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path / "workspace")})

    written = write_text_file(
        root,
        "nested/example.txt",
        "zero\none\ntwo\nthree\n",
    )
    assert written.path == "nested/example.txt"
    assert written.bytes_written == len("zero\none\ntwo\nthree\n".encode("utf-8"))

    read = read_text_file(root, "nested/example.txt", offset=1, limit=2)
    assert read.path == "nested/example.txt"
    assert read.text == "2\tone\n3\ttwo"
    assert read.offset == 1
    assert read.returned_lines == 2


def test_read_without_line_numbers(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path)})
    write_text_file(root, "plain.txt", "alpha\nbeta\n")

    read = read_text_file(root, "plain.txt", number_lines=False)
    assert read.text == "alpha\nbeta"


@pytest.mark.parametrize("raw_path", ["../outside.txt", "nested/../../outside.txt"])
def test_traversal_is_rejected(tmp_path: Path, raw_path: str) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path / "workspace")})

    with pytest.raises(WorkspacePathError, match="escapes"):
        resolve_workspace_path(root, raw_path)


def test_absolute_path_is_rejected(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path / "workspace")})

    with pytest.raises(WorkspacePathError, match="Absolute paths"):
        resolve_workspace_path(root, str(tmp_path / "outside.txt"))


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path / "workspace")})
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(WorkspacePathError, match="escapes"):
        write_text_file(root, "linked/escape.txt", "blocked")
    assert not (outside / "escape.txt").exists()


def test_missing_and_oversized_reads_are_rejected(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path)})

    with pytest.raises(ValueError, match="does not exist"):
        read_text_file(root, "missing.txt")

    oversized = root / "oversized.txt"
    oversized.write_bytes(b"x" * (DEFAULT_MAX_READ_BYTES + 1))
    with pytest.raises(ValueError, match="256 KB"):
        read_text_file(root, "oversized.txt")


def test_invalid_utf8_is_rejected(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path)})
    (root / "binary.txt").write_bytes(b"\xff\xfe")

    with pytest.raises(UnicodeDecodeError):
        read_text_file(root, "binary.txt")


def test_exact_edit_requires_unique_match_unless_replace_all(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path)})
    write_text_file(root, "edit.txt", "alpha beta alpha\n")

    with pytest.raises(ValueError, match="Found 2 matches"):
        edit_text_file(root, "edit.txt", "alpha", "omega")

    edited = edit_text_file(
        root,
        "edit.txt",
        "alpha",
        "omega",
        replace_all=True,
    )
    assert edited.replacements == 2
    assert (root / "edit.txt").read_text(encoding="utf-8") == "omega beta omega\n"


def test_edit_rejects_empty_missing_and_identical_strings(tmp_path: Path) -> None:
    root = resolve_workspace_root({"working_directory": str(tmp_path)})
    write_text_file(root, "edit.txt", "alpha\n")

    with pytest.raises(ValueError, match="must not be empty"):
        edit_text_file(root, "edit.txt", "", "omega")
    with pytest.raises(ValueError, match="must be different"):
        edit_text_file(root, "edit.txt", "alpha", "alpha")
    with pytest.raises(ValueError, match="not found"):
        edit_text_file(root, "edit.txt", "missing", "omega")