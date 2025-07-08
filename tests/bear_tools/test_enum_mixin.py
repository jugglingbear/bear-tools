"""
Comprehensive unit tests for the EnumMixin class.

This module contains type-hinted unit tests that validate all functionality
of the EnumMixin class, including edge cases and error conditions.
"""

# pylint: disable=C0117

from __future__ import annotations

from enum import Enum
from typing import Type

import pytest

from bear_tools.enum_mixin import EnumMixin


class TestEnum(EnumMixin, Enum):
    """Test enum class for testing EnumMixin functionality."""
    __test__ = False

    FIRST = 1
    SECOND = "two"
    THIRD = 3.0
    FOURTH = [4]
    FIFTH = {"five": 5}


class EmptyEnum(EnumMixin, Enum):
    """Empty enum class for testing edge cases."""


class SingleValueEnum(EnumMixin, Enum):
    """Single value enum for testing edge cases."""

    ONLY = "only_value"


class NumericEnum(EnumMixin, Enum):
    """Numeric enum for testing comparison operations."""

    LOW = 1
    MEDIUM = 5
    HIGH = 10


class TestEnumMixin:
    """Comprehensive test suite for EnumMixin class."""

    def test_all_names_returns_correct_names(self) -> None:
        """Test that all_names returns all enum member names."""
        expected_names = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH"]
        actual_names = TestEnum.all_names()

        assert actual_names == expected_names
        assert isinstance(actual_names, list)
        assert all(isinstance(name, str) for name in actual_names)

    def test_all_names_empty_enum(self) -> None:
        """Test all_names with empty enum."""
        actual_names = EmptyEnum.all_names()

        assert actual_names == []
        assert isinstance(actual_names, list)

    def test_all_names_single_value_enum(self) -> None:
        """Test all_names with single value enum."""
        expected_names = ["ONLY"]
        actual_names = SingleValueEnum.all_names()

        assert actual_names == expected_names
        assert isinstance(actual_names, list)

    def test_all_values_returns_correct_values(self) -> None:
        """Test that all_values returns all enum member values."""
        expected_values = [1, "two", 3.0, [4], {"five": 5}]
        actual_values = TestEnum.all_values()

        assert actual_values == expected_values
        assert isinstance(actual_values, list)

    def test_all_values_empty_enum(self) -> None:
        """Test all_values with empty enum."""
        actual_values = EmptyEnum.all_values()

        assert actual_values == []
        assert isinstance(actual_values, list)

    def test_all_values_single_value_enum(self) -> None:
        """Test all_values with single value enum."""
        expected_values = ["only_value"]
        actual_values = SingleValueEnum.all_values()

        assert actual_values == expected_values
        assert isinstance(actual_values, list)

    def test_contains_value_with_existing_values(self) -> None:
        """Test contains_value returns True for existing values."""
        assert TestEnum.contains_value(1) is True
        assert TestEnum.contains_value("two") is True
        assert TestEnum.contains_value(3.0) is True
        assert TestEnum.contains_value([4]) is True
        assert TestEnum.contains_value({"five": 5}) is True

    def test_contains_value_with_nonexistent_values(self) -> None:
        """Test contains_value returns False for non-existent values."""
        assert TestEnum.contains_value(999) is False
        assert TestEnum.contains_value("nonexistent") is False
        assert TestEnum.contains_value(None) is False
        assert TestEnum.contains_value([]) is False
        assert TestEnum.contains_value({}) is False

    def test_contains_value_empty_enum(self) -> None:
        """Test contains_value with empty enum."""
        assert EmptyEnum.contains_value("anything") is False
        assert EmptyEnum.contains_value(None) is False

    def test_contains_value_type_sensitivity(self) -> None:
        """Test that contains_value is type-sensitive."""
        assert TestEnum.contains_value(1) is True
        assert TestEnum.contains_value(1.0) is True  # Python treats 1 == 1.0 as True
        assert TestEnum.contains_value("1") is False
        assert TestEnum.contains_value(3.0) is True
        assert TestEnum.contains_value(3) is True  # Python treats 3 == 3.0 as True

    def test_get_item_with_valid_values(self) -> None:
        """Test get_item returns correct enum members for valid values."""
        assert TestEnum.get_item(1) == TestEnum.FIRST
        assert TestEnum.get_item("two") == TestEnum.SECOND
        assert TestEnum.get_item(3.0) == TestEnum.THIRD
        assert TestEnum.get_item([4]) == TestEnum.FOURTH
        assert TestEnum.get_item({"five": 5}) == TestEnum.FIFTH

    def test_get_item_with_invalid_values(self) -> None:
        """Test get_item returns None for invalid values."""
        assert TestEnum.get_item(999) is None
        assert TestEnum.get_item("nonexistent") is None
        assert TestEnum.get_item(None) is None
        assert TestEnum.get_item([]) is None
        assert TestEnum.get_item({}) is None

    def test_get_item_empty_enum(self) -> None:
        """Test get_item with empty enum."""
        assert EmptyEnum.get_item("anything") is None
        assert EmptyEnum.get_item(None) is None

    def test_get_item_return_type(self) -> None:
        """Test that get_item returns the correct type."""
        item = TestEnum.get_item(1)
        assert isinstance(item, TestEnum)
        assert item is not None

        none_item = TestEnum.get_item("invalid")
        assert none_item is None

    def test_get_name_with_valid_values(self) -> None:
        """Test get_name returns correct names for valid values."""
        assert TestEnum.get_name(1) == "FIRST"
        assert TestEnum.get_name("two") == "SECOND"
        assert TestEnum.get_name(3.0) == "THIRD"
        assert TestEnum.get_name([4]) == "FOURTH"
        assert TestEnum.get_name({"five": 5}) == "FIFTH"

    def test_get_name_with_invalid_values(self) -> None:
        """Test get_name returns None for invalid values."""
        assert TestEnum.get_name(999) is None
        assert TestEnum.get_name("nonexistent") is None
        assert TestEnum.get_name(None) is None
        assert TestEnum.get_name([]) is None
        assert TestEnum.get_name({}) is None

    def test_get_name_empty_enum(self) -> None:
        """Test get_name with empty enum."""
        assert EmptyEnum.get_name("anything") is None
        assert EmptyEnum.get_name(None) is None

    def test_get_name_return_type(self) -> None:
        """Test that get_name returns the correct type."""
        name = TestEnum.get_name(1)
        assert isinstance(name, str)
        assert name is not None

        none_name = TestEnum.get_name("invalid")
        assert none_name is None

    def test_hash_method(self) -> None:
        """Test that __hash__ method works correctly."""
        first_item = TestEnum.FIRST
        second_item = TestEnum.SECOND

        # Test that hash is based on name
        assert hash(first_item) == hash("FIRST")
        assert hash(second_item) == hash("SECOND")

        # Test that different enum members have different hashes
        assert hash(first_item) != hash(second_item)

        # Test that same enum member has consistent hash
        assert hash(TestEnum.FIRST) == hash(TestEnum.FIRST)

    def test_hash_method_with_same_name_different_values(self) -> None:
        """Test hash consistency for enum members."""
        # Create two references to the same enum member
        first_ref1 = TestEnum.FIRST
        first_ref2 = TestEnum.FIRST

        assert hash(first_ref1) == hash(first_ref2)
        assert first_ref1 is first_ref2  # Should be the same object

    def test_lt_method_with_numeric_values(self) -> None:
        """Test __lt__ method with numeric enum values."""
        assert NumericEnum.LOW < NumericEnum.MEDIUM
        assert NumericEnum.MEDIUM < NumericEnum.HIGH
        assert NumericEnum.LOW < NumericEnum.HIGH

        # Test reflexivity
        assert not NumericEnum.LOW < NumericEnum.LOW
        assert not NumericEnum.MEDIUM < NumericEnum.MEDIUM
        assert not NumericEnum.HIGH < NumericEnum.HIGH

    def test_lt_method_with_different_types(self) -> None:
        """Test __lt__ method with different enum types."""
        # Should return False when comparing with different enum type
        assert not TestEnum.FIRST < NumericEnum.LOW
        assert not NumericEnum.LOW < TestEnum.FIRST

    def test_lt_method_with_non_enum_types(self) -> None:
        """Test __lt__ method with non-enum types."""
        # Should return False when comparing with non-enum types
        assert not NumericEnum.LOW < 5
        assert not NumericEnum.LOW < "string"
        assert not NumericEnum.LOW < None
        assert not NumericEnum.LOW < [1, 2, 3]

    def test_lt_method_with_non_comparable_values(self) -> None:
        """Test __lt__ method with non-comparable enum values."""
        # When enum values are not comparable, should raise TypeError
        with pytest.raises(TypeError):
            # pylint: disable=W0104
            TestEnum.FIRST < TestEnum.SECOND  # type: ignore[unused-ignore]

    def test_enum_inheritance_properties(self) -> None:
        """Test that EnumMixin properly inherits from Enum."""
        assert issubclass(TestEnum, EnumMixin)
        assert isinstance(TestEnum.FIRST, TestEnum)
        assert isinstance(TestEnum.FIRST, EnumMixin)

        # Test that enum members have expected properties
        assert TestEnum.FIRST.name == "FIRST"
        assert TestEnum.FIRST.value == 1

    def test_enum_uniqueness(self) -> None:
        """Test that enum members are unique objects."""
        assert TestEnum.FIRST is TestEnum.FIRST
        assert TestEnum.FIRST is not TestEnum.SECOND  # type: ignore[comparison-overlap]

        # Test that creating enum with same value twice refers to same object
        first_ref1 = TestEnum(1)
        first_ref2 = TestEnum(1)
        assert first_ref1 is first_ref2
        assert first_ref1 is TestEnum.FIRST

    def test_edge_case_complex_data_types(self) -> None:
        """Test enum with complex data types as values."""
        # Test with list value
        list_item = TestEnum.get_item([4])
        assert list_item == TestEnum.FOURTH
        assert TestEnum.contains_value([4]) is True

        # Test with dict value
        dict_item = TestEnum.get_item({"five": 5})
        assert dict_item == TestEnum.FIFTH
        assert TestEnum.contains_value({"five": 5}) is True

    def test_method_return_types_are_correct(self) -> None:
        """Test that all methods return the expected types."""
        # all_names should return list[str]
        names = TestEnum.all_names()
        assert isinstance(names, list)
        assert all(isinstance(name, str) for name in names)

        # all_values should return list[Any]
        values = TestEnum.all_values()
        assert isinstance(values, list)

        # contains_value should return bool
        result = TestEnum.contains_value(1)
        assert isinstance(result, bool)

        # get_item should return T | None
        item = TestEnum.get_item(1)
        assert item is None or isinstance(item, TestEnum)

        # get_name should return str | None
        name = TestEnum.get_name(1)
        assert name is None or isinstance(name, str)

    def test_integration_with_standard_enum_features(self) -> None:
        """Test that EnumMixin works with standard Enum features."""
        # Test iteration
        enum_members = list(TestEnum)
        assert len(enum_members) == 5
        assert TestEnum.FIRST in enum_members

        # Test membership
        assert TestEnum.FIRST in TestEnum

        # Test string representation
        assert str(TestEnum.FIRST) == "TestEnum.FIRST"
        assert repr(TestEnum.FIRST) == "<TestEnum.FIRST: 1>"

    @pytest.mark.parametrize("enum_class", [TestEnum, SingleValueEnum])
    def test_all_methods_with_different_enum_classes(self, enum_class: Type[EnumMixin]) -> None:
        """Test all methods work with different enum classes."""
        # Test that methods don't crash with different enum types
        names = enum_class.all_names()
        values = enum_class.all_values()

        assert isinstance(names, list)
        assert isinstance(values, list)
        assert len(names) == len(values)

        if names:  # If enum has members
            first_value = values[0]
            assert enum_class.contains_value(first_value) is True
            assert enum_class.get_item(first_value) is not None
            assert enum_class.get_name(first_value) is not None

    def test_type_var_bound_constraint(self) -> None:
        """Test that type variable T is properly bound to EnumMixin."""
        # This is more of a static type checking test, but we can verify runtime behavior
        item = TestEnum.get_item(1)
        if item is not None:
            assert isinstance(item, EnumMixin)
            assert isinstance(item, TestEnum)
