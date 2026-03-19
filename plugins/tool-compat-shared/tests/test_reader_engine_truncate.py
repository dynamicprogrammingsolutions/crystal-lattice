from __future__ import annotations

from pathlib import Path

from tool_compat_shared.reader_engine import format_with_line_numbers, truncate_line


def test_truncate_line_short_line_unchanged() -> None:
    assert truncate_line("hello", 10, marker="...") == "hello"


def test_truncate_line_exact_length_unchanged() -> None:
    assert truncate_line("hello", 5, marker="...") == "hello"


def test_truncate_line_long_line_truncated() -> None:
    # Total output = max_length (content + marker)
    result = truncate_line("abcdefghij", 7, marker="...")
    assert result == "abcd..."  # 4 + 3 = 7
    assert len(result) == 7


def test_truncate_line_preserves_trailing_newline() -> None:
    # Linebreak is extracted and re-appended after the marker
    # max_length applies to the content+marker part (without linebreak)
    # Total: line[:max_length - len(marker)] + marker + linebreak
    result = truncate_line("abcdefghij\n", 7, marker="...")
    # end = "...\n" (len 4), effective_max = max(7, 4) = 7
    # line[:7-4] + "...\n" = line[:3] + "...\n" = "abc...\n"
    assert result == "abc...\n"


def test_truncate_line_preserves_trailing_carriage_newline() -> None:
    result = truncate_line("abcdefghij\r\n", 7, marker="...")
    # end = "...\r\n" (len 5), effective_max = max(7, 5) = 7
    # line[:7-5] + "...\r\n" = line[:2] + "...\r\n" = "ab...\r\n"
    assert result == "ab...\r\n"


def test_truncate_line_custom_marker() -> None:
    result = truncate_line("abcdefghij", 8, marker="[cut]")
    # end = "[cut]" (len 5), effective_max = max(8, 5) = 8
    # line[:8-5] + "[cut]" = line[:3] + "[cut]" = "abc[cut]"
    assert result == "abc[cut]"


def test_truncate_line_empty_string() -> None:
    assert truncate_line("", 10) == ""


def test_format_with_line_numbers_basic() -> None:
    lines = ["first", "second", "third"]
    result = format_with_line_numbers(lines, start_line=1, width=6)
    assert result == "     1\tfirst\n     2\tsecond\n     3\tthird\n"


def test_format_with_line_numbers_custom_start() -> None:
    lines = ["alpha", "beta"]
    result = format_with_line_numbers(lines, start_line=42, width=6)
    assert result == "    42\talpha\n    43\tbeta\n"


def test_format_with_line_numbers_wider_width() -> None:
    lines = ["x"]
    result = format_with_line_numbers(lines, start_line=1, width=8)
    assert result == "       1\tx\n"


def test_format_with_line_numbers_empty_list() -> None:
    assert format_with_line_numbers([], start_line=1, width=6) == ""
