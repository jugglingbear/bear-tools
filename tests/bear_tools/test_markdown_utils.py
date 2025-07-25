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
