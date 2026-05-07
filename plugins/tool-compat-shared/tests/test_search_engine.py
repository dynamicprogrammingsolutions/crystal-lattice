from __future__ import annotations

import os
import time
from pathlib import Path

import tool_compat_shared.search_engine as search_engine
from tool_compat_shared.reader_engine import DEFAULT_GEMINI_LINE_CHAR_LIMIT
from tool_compat_shared.search_engine import format_gemini_grep_result, glob_search, grep_search, list_directory_entries


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


def test_grep_search_does_not_fallback_when_ripgrep_returns_no_matches(monkeypatch, tmp_path: Path) -> None:
    def fake_run_ripgrep(*args, **kwargs):
        return {"ok": True, "stdout": "", "names_only": False, "count_mode": False, "cwd": str(tmp_path)}

    def fail_iter_files(*args, **kwargs):
        raise AssertionError("fallback should not run after a successful ripgrep no-match result")

    monkeypatch.setattr(search_engine, "_run_ripgrep", fake_run_ripgrep)
    monkeypatch.setattr(search_engine, "_iter_files", fail_iter_files)

    outcome = grep_search("nomatch", search_path=str(tmp_path), display_root=str(tmp_path))

    assert outcome["ok"] is True
    assert outcome["results"] == []
    assert outcome["used_rg"] is True


def test_format_gemini_grep_result_truncates_long_lines() -> None:
    long_line = "x" * (DEFAULT_GEMINI_LINE_CHAR_LIMIT + 500)
    outcome = {
        "ok": True,
        "results": [
            {"path": "/tmp/big.sql", "line_number": 110, "line": long_line},
            {"path": "/tmp/big.sql", "line_number": 111, "line": "short line"},
        ],
        "used_rg": False,
    }
    result = format_gemini_grep_result(outcome, pattern="x", search_description="in the workspace directory", names_only=False)
    assert result["success"] is True
    body = result["result"]
    # The long line should be truncated with the marker
    assert "... [truncated]" in body
    # The short line should appear intact
    assert "short line" in body
    # The truncated line should not contain the full 2500 chars
    assert long_line not in body
    # return_display should note the shortening
    assert "some lines were shortened" in result["return_display"]


def test_format_gemini_grep_result_no_truncation_for_short_lines() -> None:
    outcome = {
        "ok": True,
        "results": [
            {"path": "/tmp/a.txt", "line_number": 1, "line": "hello world"},
        ],
        "used_rg": False,
    }
    result = format_gemini_grep_result(outcome, pattern="hello", search_description="in the workspace directory", names_only=False)
    assert result["success"] is True
    assert "hello world" in result["result"]
    assert "... [truncated]" not in result["result"]
    assert "some lines were shortened" not in result["return_display"]


def test_format_gemini_grep_result_truncates_at_exact_boundary() -> None:
    # Line exactly at the limit should NOT be truncated
    exact_line = "a" * DEFAULT_GEMINI_LINE_CHAR_LIMIT
    outcome = {
        "ok": True,
        "results": [
            {"path": "/tmp/b.txt", "line_number": 1, "line": exact_line},
        ],
        "used_rg": False,
    }
    result = format_gemini_grep_result(outcome, pattern="a", search_description="in the workspace directory", names_only=False)
    assert "... [truncated]" not in result["result"]

    # Line one char over the limit should be truncated
    over_line = "a" * (DEFAULT_GEMINI_LINE_CHAR_LIMIT + 1)
    outcome2 = {
        "ok": True,
        "results": [
            {"path": "/tmp/c.txt", "line_number": 1, "line": over_line},
        ],
        "used_rg": False,
    }
    result2 = format_gemini_grep_result(outcome2, pattern="a", search_description="in the workspace directory", names_only=False)
    assert "... [truncated]" in result2["result"]
