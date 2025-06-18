# flake8: noqa: E501
# pylint: disable=C0301

"""
Test functions in bear_tools/misc_functions.py
"""

from collections.abc import Callable

import pytest

from bear_tools.misc_utils import do_nothing


def test_do_nothing_returns_none() -> None:
    """Verify that the do_nothing API returns None"""
    result: None = do_nothing()  # type: ignore[func-returns-value]
    assert result is None


def test_do_nothing_with_positional_args() -> None:
    """Verify that do_nothing returns None when sent positional arguments"""
    result: None = do_nothing(1, 2.0, "abc", [1, 2], (3, 4), {5, 6}, {"key": "value"})  # type: ignore[func-returns-value]
    assert result is None


def test_do_nothing_with_keyword_args() -> None:
    """Verify that do_nothing returns None with keyword arguments"""
    result: None = do_nothing(a=1, b="two", c=[3], d={"four": 4}, e=(5,), f=True, g=None)  # type: ignore[func-returns-value]
    assert result is None


def test_do_nothing_with_both_args() -> None:
    """Verify that do_nothing returns None when sent data in both args and kwargs"""
    result: None = do_nothing(42, "foo", x=3.14, y=False)  # type: ignore[func-returns-value]
    assert result is None


def test_do_nothing_used_as_callback() -> None:
    """Verify that do_nothing can be used as a callback"""
    def call_callback(cb: Callable[..., None]) -> None:
        result: None = cb("some arg", another="value")  # type: ignore[func-returns-value]
        assert result is None

    call_callback(do_nothing)


def test_do_nothing_does_not_raise() -> None:
    """Verify that do_nothing does not raise any exceptions"""
    try:
        result: None = do_nothing(object(), 123, name="test", callback=lambda: "noop", config={"enabled": True})  # type: ignore[func-returns-value]
        assert result is None
    except Exception as exc:  # pylint: disable=W0718
        pytest.fail(f"do_nothing raised an unexpected exception: {exc}")
