import pytest
import tempfile
from bear_tools.lumberjack import get_color_str, PrintColor, print_color

test_messages: list = ['test', 123, 456.7, ['cats'], {'key':890}]


def test_get_color_str() -> None:
    for _message in test_messages:
        for _color in PrintColor:
            s = get_color_str(message=_message, color=_color)  # type: ignore
            assert isinstance(s, str)


def test_PrintColor() -> None:
    for _enum in PrintColor:
        assert isinstance(_enum.value, str)


def test_print_color() -> None:
    # def print_color(message: str, color: str, path: TextIO = sys.stdout, end: str ='\n') -> None:
    temp = tempfile.TemporaryFile('w')
    for _message in test_messages:
        for _color in PrintColor:
            try:
                print_color(message=_message, color=_color)
            except:
                pytest.fail('Exception occurred during call to print_color')

