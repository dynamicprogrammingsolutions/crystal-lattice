from __future__ import annotations

import os
import time
from pathlib import Path

from tool_compat_shared.search_engine import glob_search, grep_search, list_directory_entries


def test_list_directory_entries_counts_git_and_vendor_ignores(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("ignored-git.txt\n", encoding="utf-8")
    (tmp_path / ".geminiignore").write_text("ignored-vendor.txt\n", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("keep\n", encoding="utf-8")
    (tmp_path / "ignored-git.txt").write_text("git\n", encoding="utf-8")
    (tmp_path / "ignored-vendor.txt").write_text("vendor\n", encoding="utf-8")
    (tmp_path / "skip.tmp").write_text("tmp\n", encoding="utf-8")
    (tmp_path / "nested").mkdir()

    outcome = list_directory_entries(
        str(tmp_path),
        display_root=str(tmp_path),
        ignore_patterns=["*.tmp"],
        vendor_ignore_filename=".geminiignore",
    )

    assert outcome["ok"] is True
    assert [entry["name"] for entry in outcome["entries"]] == ["nested", ".geminiignore", ".gitignore", "keep.txt"]
    assert outcome["git_ignored_count"] == 1
    assert outcome["vendor_ignored_count"] == 1


def test_glob_search_sorts_recent_files_first_and_matches_case_insensitively(tmp_path: Path) -> None:
    folder = tmp_path / "folder"
    folder.mkdir()
    recent = folder / "recent.txt"
    older = folder / "older.txt"
    upper = folder / "UPPER.TXT"
    recent.write_text("recent\n", encoding="utf-8")
    older.write_text("older\n", encoding="utf-8")
    upper.write_text("upper\n", encoding="utf-8")
    now = time.time()
    os.utime(recent, (now, now))
    os.utime(upper, (now - 10, now - 10))
    old = now - (3 * 24 * 60 * 60)
    os.utime(older, (old, old))

    outcome = glob_search(
        "folder/*.txt",
        search_directories=[str(tmp_path)],
        display_root=str(tmp_path),
        case_sensitive=False,
    )

    assert outcome["ok"] is True
    assert outcome["paths"] == [str(recent.resolve()), str(upper.resolve()), str(older.resolve())]


def test_grep_search_python_fallback_respects_glob_filter(tmp_path: Path) -> None:
    (tmp_path / "alpha.txt").write_text("token here\n", encoding="utf-8")
    (tmp_path / "beta.py").write_text("token here too\n", encoding="utf-8")

    outcome = grep_search(
        "token",
        search_path=str(tmp_path),
        display_root=str(tmp_path),
        glob_pattern="*.txt",
        ignore_case=True,
        use_rg=False,
    )

    assert outcome["ok"] is True
    assert outcome["results"] == [
        {"path": str((tmp_path / "alpha.txt").resolve()), "line_number": 1, "line": "token here"}
    ]
