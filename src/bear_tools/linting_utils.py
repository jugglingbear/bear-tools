"""
A collection of linting-related utilities
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar('T')


def assert_not_none(value: T | None, message: str = 'Value cannot be None') -> T:
    """
    Assert that a given value is not None for static type chekers
    """

    assert value is not None, message
    return value
