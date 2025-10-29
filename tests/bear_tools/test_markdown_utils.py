# flake8: noqa: E501
# pylint: disable=C0116

"""
Unit tests for bear_tools.markdown_utils
"""

from __future__ import annotations

import pytest

from bear_tools.markdown_utils import emoji, get_table


def test_emoji_true_returns_checkmark() -> None:
    """Verify that True returns a ✅"""
    result: str = emoji(True)
    assert result == "✅"


def test_emoji_false_returns_cross() -> None:
    """Verify that False returns a ❌"""
    result: str = emoji(False)
    assert result == "❌"


def test_get_table_basic_table() -> None:
    """Verify that a basic 2x2 table is generated correctly"""
    data: list[list[str]] = [
        ["row1col1", "row1col2"],
        ["row2col1", "row2col2"]
    ]
    expected: str = (
        "| row1col1 | row1col2 |\n"
        "|----------|----------|\n"
        "| row2col1 | row2col2 |"
    )
    result: str = get_table(data)
    assert result == expected


def test_get_table_handles_varying_column_widths() -> None:
    """Verify that columns adjust to the longest item in each column"""
    data: list[list[str]] = [
        ["short", "tiny"],
        ["much_longer_text", "medium"]
    ]
    expected: str = (
        "| short            | tiny   |\n"
        "|------------------|--------|\n"
        "| much_longer_text | medium |"
    )
    result: str = get_table(data)
    assert result == expected


def test_get_table_with_single_row() -> None:
    """Verify that tables with only a header row still render correctly"""
    data: list[list[str]] = [["only", "header"]]
    expected: str = (
        "| only | header |\n"
        "|------|--------|"
    )
    result: str = get_table(data)
    assert result == expected


def test_get_table_raises_value_error_on_empty_input() -> None:
    """Verify that an empty list raises ValueError"""
    with pytest.raises(ValueError, match="Input should be a list\\[list\\[str\\]\\]"):
        get_table([])


def test_get_table_raises_value_error_on_non_list_rows() -> None:
    """Verify that non-list rows raise ValueError"""
    with pytest.raises(ValueError):
        get_table(["not", "a", "2d", "list"])  # type: ignore[list-item]


def test_get_table_with_numbers_casts_to_string() -> None:
    """Verify that numeric values are safely converted to strings"""
    data: list[list[str]] = [[str(123), str(45)]]
    expected: str = (
        "| 123 | 45 |\n"
        "|-----|----|"
    )
    result: str = get_table(data)
    assert result == expected


def test_get_table_handles_none_and_uneven_rows() -> None:
    """Verify None becomes empty string and uneven rows are padded"""
    data: list[list[str]] = [
        ["head1", "head2", "head3"],
        [None, "x"],                 # shorter row, None -> ""
        ["a", "bb", "ccc"],
    ]
    expected: str = (
        "| head1 | head2 | head3 |\n"
        "|-------|-------|-------|\n"
        "|       | x     |       |\n"
        "| a     | bb    | ccc   |"
    )
    result: str = get_table(data)
    assert result == expected


def test_get_table_wide_emoji_alignment() -> None:
    """
    Verify proper alignment when cells contain wide emoji.
    Emoji like 😀 have a display width of 2; header should dictate column width.
    """
    data: list[list[str]] = [
        ["col1", "col2"],
        ["😀", "x"],
        ["a", "yy"],
    ]
    expected: str = (
        "| col1 | col2 |\n"
        "|------|------|\n"
        "| 😀   | x    |\n"
        "| a    | yy   |"
    )
    result: str = get_table(data)
    assert result == expected


def test_get_table_cjk_wide_chars_alignment() -> None:
    """
    Verify proper alignment with CJK wide characters (e.g., '漢' and '字' are width 2).
    """
    data: list[list[str]] = [
        ["h", "c"],
        ["漢", "字"],
        ["ab", "z"],
    ]
    expected: str = (
        "| h  | c  |\n"
        "|----|----|\n"
        "| 漢 | 字 |\n"
        "| ab | z  |"
    )
    result: str = get_table(data)
    assert result == expected


def test_get_table_ansi_sequences_do_not_break_alignment() -> None:
    """
    Verify ANSI color codes don't affect column width calculations.
    First column has visible width 3 ('red'), despite escape sequences.
    """
    red_ansi: str = "\x1b[31mred\x1b[0m"
    data: list[list[str]] = [
        ["h", "c"],
        [red_ansi, "x"],
    ]
    expected: str = (
        "| h   | c |\n"
        "|-----|---|\n"
        f"| {red_ansi} | x |"
    )
    result: str = get_table(data)
    assert result == expected
