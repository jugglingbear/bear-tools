from __future__ import annotations

from enum import Enum
from typing import Any, Type, TypeVar


class EnumMixin(Enum):
    """
    A mixin for enum.Enum subclasses that provides convenient APIs
    """

    @classmethod
    def all_names(cls: Type[T]) -> list[str]:
        """
        Get all variable names associated with the enum
        """

        return [_enum.name for _enum in cls]


    @classmethod
    def all_values(cls: Type[T]) -> list[Any]:
        """
        Get all values associated with the enum
        """

        return [_enum.value for _enum in cls]


    @classmethod
    def contains_value(cls: Type[T], value: Any) -> bool:
        """
        Returns True if one of the enumerated values is equal to the given value; False otherwise
        """

        return any(value == _enum.value for _enum in cls)


    @classmethod
    def get_item(cls: Type[T], value: Any) -> T | None:
        """
        Get an item from the enumerated class
        """

        try:
            return cls(value)
        except ValueError:
            return None


    @classmethod
    def get_name(cls: Type[T], value: Any) -> str | None:
        """
        Get the name associated with a given enum value
        """

        try:
            return cls(value).name
        except ValueError:
            return None


    def __hash__(self: Enum) -> int:
        return hash(self.name)


    def __lt__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.value < other.value


T = TypeVar('T', bound=EnumMixin)

__all__ = [
    'EnumMixin'
]
