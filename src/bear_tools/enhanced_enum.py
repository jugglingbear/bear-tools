from __future__ import annotations

from enum import Enum
from typing import Any, Type, TypeVar, cast

T = TypeVar("T", bound="EnhancedEnum")


class EnhancedEnum(Enum):
    """
    An enhancement to the Enum class that adds useful convenience methods

    All collection-returning methods preserve member definition order.
    """

    @classmethod
    def names(cls: Type[T]) -> list[str]:
        """Return the names of all members, in definition order."""
        return [m.name for m in cls]

    @classmethod
    def members(cls: Type[T]) -> list[T]:
        """Return all enum members (instances), in definition order."""
        return list(cls)

    @classmethod
    def values(cls: Type[T]) -> list[Any]:
        """Return the values of all members, in definition order."""
        return [m.value for m in cls]

    @classmethod
    def contains_value(cls: Type[T], value: Any) -> bool:
        """Return True if any member's value equals `value`; otherwise False."""
        return any(value == m.value for m in cls)

    @classmethod
    def get_member(cls: Type[T], value: Any) -> T | None:
        """Return the member whose value equals `value`, or None if not found."""
        try:
            return cls(value)
        except ValueError:
            return None

    @classmethod
    def get_name(cls: Type[T], value: Any) -> str | None:
        """Return the member name for `value`, or None if not found."""
        try:
            return cls(value).name
        except ValueError:
            return None


    def __lt__(self, other: Any) -> bool:
        """
        Define ordering by underlying values when comparing members of the same enum.
        For cross-type comparisons or non-comparable values, defer via NotImplemented.
        """
        if not isinstance(other, self.__class__):
            return NotImplemented
        try:
            return cast(bool, self.value < other.value)
        except TypeError:
            return NotImplemented


__all__ = ["EnhancedEnum"]
