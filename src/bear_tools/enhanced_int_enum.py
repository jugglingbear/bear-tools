from __future__ import annotations

from enum import IntEnum
from typing import Any, Type, TypeVar

T = TypeVar("T", bound="EnhancedIntEnum")


class EnhancedIntEnum(IntEnum):
    """
    An enhancement to the IntEnum class that adds useful convenience methods

    All collection-returning methods preserve member definition order.
    """

    # ----- Collection helpers -----

    @classmethod
    def names(cls: Type[T]) -> list[str]:
        """Return the names of all members, in definition order."""
        return [m.name for m in cls]

    @classmethod
    def members(cls: Type[T]) -> list[T]:
        """Return all enum members (instances), in definition order."""
        return list(cls)

    @classmethod
    def values(cls: Type[T]) -> list[int]:
        """Return the integer values of all members, in definition order."""
        return [m.value for m in cls]

    # ----- Lookup helpers -----

    @classmethod
    def contains_value(cls: Type[T], value: Any) -> bool:
        """Return True if any member's value equals `value`; otherwise False."""
        return any(value == m.value for m in cls)

    @classmethod
    def get_member(cls: Type[T], value: Any) -> T | None:
        """Return the member whose value equals `value`, or None if not found."""
        try:
            return cls(value)
        except (ValueError, TypeError):
            return None

    @classmethod
    def get_name(cls: Type[T], value: Any) -> str | None:
        """Return the member name for `value`, or None if not found."""
        try:
            return cls(value).name
        except (ValueError, TypeError):
            return None


__all__ = ["EnhancedIntEnum"]
