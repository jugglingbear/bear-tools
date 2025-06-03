# pylint: disable=C0103
# pylint: disable=W0718

import tempfile
from typing import Any

import pytest

from bear_tools.lumberjack import PrintColor, get_color_str, print_color

test_messages: list[Any] = ['test', 123, 456.7, ['cats'], {'key': 890}]


def test_get_color_str() -> None:
    """test the get_color_str API"""
    for _message in test_messages:
        for _color in PrintColor:
            s = get_color_str(message=_message, color=_color)
            assert isinstance(s, str)


def test_PrintColor() -> None:
    """Test the PrintColor API"""
    for _enum in PrintColor:
        assert isinstance(_enum.value, str)


def test_print_color() -> None:
    """Test the print_color API"""
    # def print_color(message: str, color: str, path: TextIO = sys.stdout, end: str ='\n') -> None:
    temp = tempfile.TemporaryFile('w')
    for _message in test_messages:
        for _color in PrintColor:
            try:
                print_color(message=_message, color=_color)
            except Exception:
                pytest.fail('Exception occurred during call to print_color')
