# pylint: disable=C0115

"""
Unit tests for assert_not_none in bear_tools/linting_utils.py
"""

import pytest

from bear_tools.linting_utils import assert_not_none


def test_returns_same_value_for_non_none() -> None:
    """Verify that the function returns the same non-None value"""
    value: int = 42
    result: int = assert_not_none(value)
    assert result == 42
    assert result is value  # Identity check


def test_works_with_various_types() -> None:
    """Verify correct behavior with multiple types"""
    assert assert_not_none("hello") == "hello"
    assert assert_not_none(3.14) == 3.14
    assert assert_not_none([1, 2, 3]) == [1, 2, 3]
    assert assert_not_none({"key": "value"}) == {"key": "value"}


def test_works_with_custom_object() -> None:
    """Verify correct behavior with a custom object type"""

    class Dummy:
        def __init__(self, x: int) -> None:
            self.x = x

    obj: Dummy = Dummy(10)
    result: Dummy = assert_not_none(obj)
    assert result.x == 10
    assert result is obj


def test_raises_assertion_error_for_none() -> None:
    """Verify that the function raises AssertionError when value is None"""
    with pytest.raises(AssertionError, match="Value cannot be None"):
        assert_not_none(None)


def test_raises_assertion_error_with_custom_message() -> None:
    """Verify that the custom assertion message is used"""
    with pytest.raises(AssertionError, match="Custom error!"):
        assert_not_none(None, message="Custom error!")


def test_type_narrowing_hint() -> None:
    """
    Verify that the return type is correctly narrowed for type checkers.

    (At runtime, this just checks the returned value;
    static type checkers should recognize that the result is not Optional.)
    """
    value: int | None = 5
    narrowed_value: int = assert_not_none(value)
    assert isinstance(narrowed_value, int)
