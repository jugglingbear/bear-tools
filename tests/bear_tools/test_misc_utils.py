# flake8: noqa: E501
# pylint: disable=C0301

"""
Test functions in bear_tools/misc_utils.py
"""

from __future__ import annotations

import operator
from collections.abc import Callable
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from bear_tools.misc_utils import (
    do_nothing,
    get_number_of_bytes,
    int2bytearray,
    is_subsequence,
    wait_for_nested_property,
    wait_for_property,
)

# ----------------------------------------------------------------------------------------
# Existing tests for do_nothing
# ----------------------------------------------------------------------------------------

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


# ----------------------------------------------------------------------------------------
# Tests for get_number_of_bytes
# ----------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 1),
        (1, 1),
        (255, 1),
        (256, 2),
        (65535, 2),
        (65536, 3),
    ],
)
def test_get_number_of_bytes(value: int, expected: int) -> None:
    """Verify correct byte count for various integers"""
    assert get_number_of_bytes(value) == expected


# ----------------------------------------------------------------------------------------
# Tests for int2bytearray
# ----------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("value", "byteorder", "expected"),
    [
        (255, "big", bytearray(b"\xff")),
        (256, "big", bytearray(b"\x01\x00")),
        (256, "little", bytearray(b"\x00\x01")),
        (65535, "big", bytearray(b"\xff\xff")),
    ],
)
def test_int2bytearray(value: int, byteorder: str, expected: bytearray) -> None:
    """Verify correct bytearray conversion"""
    result = int2bytearray(value, byteorder)
    assert isinstance(result, bytearray)
    assert result == expected


# ----------------------------------------------------------------------------------------
# Tests for is_subsequence
# ----------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ([1, 2], [1, 2, 3], True),
        ([2, 3], [1, 2, 3], True),
        ([1, 3], [1, 2, 3], True),
        ([3, 2], [1, 2, 3], False),
        ([], [1, 2, 3], True),
        ([1, 4], [1, 2, 3], False),
    ],
)
def test_is_subsequence(a: list[int], b: list[int], expected: bool) -> None:
    """Verify subsequence detection"""
    assert is_subsequence(a, b) == expected


# ----------------------------------------------------------------------------------------
# Tests for wait_for_nested_property
# ----------------------------------------------------------------------------------------

def test_wait_for_nested_property_success_immediate() -> None:
    """Verify immediate success when property already matches expected value"""
    obj = SimpleNamespace(inner=SimpleNamespace(prop=42))
    assert wait_for_nested_property(obj, ["inner", "prop"], operator.eq, 42, timeout=0.5, cooldown=0.1)


@patch("time.sleep", return_value=None)
def test_wait_for_nested_property_success_delayed(mock_sleep: MagicMock) -> None:
    """Verify delayed success when property eventually matches expected value"""
    obj = SimpleNamespace(inner=SimpleNamespace(prop=0))

    def increment_value() -> None:
        obj.inner.prop = 5

    # Simulate property change on third check
    with patch("time.perf_counter", side_effect=[0.0, 0.1, 0.2, 0.3]):
        increment_value()
        assert wait_for_nested_property(obj, ["inner", "prop"], operator.eq, 5, timeout=1.0, cooldown=0.1)


@patch("time.sleep", return_value=None)
def test_wait_for_nested_property_timeout(mock_sleep: MagicMock) -> None:
    """Verify timeout occurs if property never matches expected value"""
    obj = SimpleNamespace(inner=SimpleNamespace(prop=1))
    with patch("time.perf_counter", side_effect=[0.0, 0.2, 0.4, 0.6, 1.2]):
        assert not wait_for_nested_property(obj, ["inner", "prop"], operator.eq, 99, timeout=1.0, cooldown=0.1)


def test_wait_for_nested_property_invalid_timeout_and_cooldown() -> None:
    """Verify ValueError raised for zero or negative timeout/cooldown"""
    obj = SimpleNamespace(prop=1)
    with pytest.raises(ValueError):
        wait_for_nested_property(obj, ["prop"], timeout=0)
    with pytest.raises(ValueError):
        wait_for_nested_property(obj, ["prop"], cooldown=0)


def test_wait_for_nested_property_empty_property_list() -> None:
    """Verify ValueError raised if property list is empty"""
    obj = SimpleNamespace()
    with pytest.raises(ValueError):
        wait_for_nested_property(obj, [])


def test_wait_for_nested_property_missing_property() -> None:
    """Verify False returned when property does not exist"""
    obj = SimpleNamespace(inner=SimpleNamespace())
    assert not wait_for_nested_property(obj, ["inner", "does_not_exist"], timeout=0.5, cooldown=0.1)


# ----------------------------------------------------------------------------------------
# Tests for wait_for_property (wrapper around wait_for_nested_property)
# ----------------------------------------------------------------------------------------

def test_wait_for_property_success() -> None:
    """Verify wait_for_property returns True when property matches expected value"""
    obj = SimpleNamespace(prop=10)
    assert wait_for_property(obj, "prop", operator.eq, 10, timeout=0.5, cooldown_time=0.1)


@patch("time.sleep", return_value=None)
def test_wait_for_property_timeout(mock_sleep: MagicMock) -> None:
    """Verify wait_for_property returns False after timeout"""
    obj = SimpleNamespace(prop=0)
    with patch("time.perf_counter", side_effect=[0.0, 0.2, 0.4, 1.2]):
        assert not wait_for_property(obj, "prop", operator.eq, 1, timeout=1.0, cooldown_time=0.1)
