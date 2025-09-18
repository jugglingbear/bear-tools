"""
Comprehensive unit tests for the EnhancedIntEnum class.

This module contains type-hinted unit tests that validate all functionality
of the EnhancedIntEnum class, including edge cases and error conditions.
"""

# pylint: disable=C0117

from __future__ import annotations

from typing import Type

import pytest

from bear_tools.enhanced_int_enum import EnhancedIntEnum


class TestIntEnum(EnhancedIntEnum):
    """Test enum class for testing EnhancedIntEnum functionality."""
    __test__ = False  # prevent pytest from collecting this enum as a test class

    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
    FIFTH = 5


class EmptyEnum(EnhancedIntEnum):
    """Empty enum class for testing edge cases."""
    __test__ = False


class SingleValueEnum(EnhancedIntEnum):
    """Single value enum for testing edge cases."""
    __test__ = False

    ONLY = 42


class NumericEnum(EnhancedIntEnum):
    """Numeric enum for testing comparison operations."""
    __test__ = False

    LOW = 1
    MEDIUM = 5
    HIGH = 10


class TestEnhancedIntEnum:
    """Comprehensive test suite for EnhancedIntEnum class."""

    def test_names_returns_correct_names(self) -> None:
        """Test that names returns all enum member names."""
        expected_names = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH"]
        actual_names = TestIntEnum.names()

        assert actual_names == expected_names
        assert isinstance(actual_names, list)
        assert all(isinstance(name, str) for name in actual_names)

    def test_names_empty_enum(self) -> None:
        """Test names with empty enum."""
        actual_names = EmptyEnum.names()

        assert actual_names == []
        assert isinstance(actual_names, list)

    def test_names_single_value_enum(self) -> None:
        """Test names with single value enum."""
        expected_names = ["ONLY"]
        actual_names = SingleValueEnum.names()

        assert actual_names == expected_names
        assert isinstance(actual_names, list)

    def test_members_returns_members_in_order(self) -> None:
        """members returns enum instances in definition order."""
        actual_members = TestIntEnum.members()
        assert actual_members == [
            TestIntEnum.FIRST,
            TestIntEnum.SECOND,
            TestIntEnum.THIRD,
            TestIntEnum.FOURTH,
            TestIntEnum.FIFTH,
        ]
        assert isinstance(actual_members, list)
        assert all(isinstance(m, TestIntEnum) for m in actual_members)

    def test_members_empty_enum(self) -> None:
        """Test members with empty enum."""
        assert EmptyEnum.members() == []

    def test_members_single_value_enum(self) -> None:
        """Test members with single value enum."""
        assert SingleValueEnum.members() == [SingleValueEnum.ONLY]

    def test_values_returns_values_in_order(self) -> None:
        """values returns raw values in definition order."""
        expected_values = [1, 2, 3, 4, 5]
        assert TestIntEnum.values() == expected_values

    def test_values_empty_enum(self) -> None:
        """Test values with empty enum."""
        assert EmptyEnum.values() == []

    def test_values_single_value_enum(self) -> None:
        """Test values with single value enum."""
        assert SingleValueEnum.values() == [42]

    def test_contains_value_with_existing_values(self) -> None:
        """Test contains_value returns True for existing values."""
        assert TestIntEnum.contains_value(1) is True
        assert TestIntEnum.contains_value(3) is True
        assert TestIntEnum.contains_value(5) is True

    def test_contains_value_with_nonexistent_values(self) -> None:
        """Test contains_value returns False for non-existent values."""
        assert TestIntEnum.contains_value(999) is False
        assert TestIntEnum.contains_value(-1) is False
        assert TestIntEnum.contains_value(None) is False

    def test_contains_value_type_sensitivity(self) -> None:
        """
        Test that contains_value follows Python equality semantics.
        IntEnum values are ints, so 1 == 1.0 is True; "1" is False.
        """
        assert TestIntEnum.contains_value(1) is True
        assert TestIntEnum.contains_value(1.0) is True  # 1 == 1.0 in Python
        assert TestIntEnum.contains_value("1") is False

    def test_get_member_with_valid_values(self) -> None:
        """Test get_member returns correct enum members for valid values."""
        assert TestIntEnum.get_member(1) == TestIntEnum.FIRST
        assert TestIntEnum.get_member(3) == TestIntEnum.THIRD
        assert TestIntEnum.get_member(5) == TestIntEnum.FIFTH

    def test_get_member_with_invalid_values(self) -> None:
        """Test get_member returns None for invalid values."""
        assert TestIntEnum.get_member(999) is None
        assert TestIntEnum.get_member(None) is None
        assert TestIntEnum.get_member(-1) is None

    def test_get_member_empty_enum(self) -> None:
        """Test get_member with empty enum."""
        assert EmptyEnum.get_member(0) is None
        assert EmptyEnum.get_member(None) is None

    def test_get_member_return_type(self) -> None:
        """Test that get_member returns the correct type."""
        item = TestIntEnum.get_member(1)
        assert isinstance(item, TestIntEnum)
        assert item is not None

        none_item = TestIntEnum.get_member(123456)
        assert none_item is None

    def test_get_name_with_valid_values(self) -> None:
        """Test get_name returns correct names for valid values."""
        assert TestIntEnum.get_name(1) == "FIRST"
        assert TestIntEnum.get_name(3) == "THIRD"
        assert TestIntEnum.get_name(5) == "FIFTH"

    def test_get_name_with_invalid_values(self) -> None:
        """Test get_name returns None for invalid values."""
        assert TestIntEnum.get_name(999) is None
        assert TestIntEnum.get_name(None) is None
        assert TestIntEnum.get_name(-1) is None

    def test_get_name_empty_enum(self) -> None:
        """Test get_name with empty enum."""
        assert EmptyEnum.get_name(0) is None
        assert EmptyEnum.get_name(None) is None

    def test_hash_method(self) -> None:
        """Test hashing behavior is stable and consistent for members."""
        first_item = TestIntEnum.FIRST
        second_item = TestIntEnum.SECOND

        # Stable and consistent hashing for same member
        assert hash(first_item) == hash(TestIntEnum.FIRST)

        # Different members typically hash differently
        assert hash(first_item) != hash(second_item)

    def test_hash_method_with_same_member_identity(self) -> None:
        """Same member should hash identically each time."""
        assert hash(TestIntEnum.FIRST) == hash(TestIntEnum.FIRST)

    def test_lt_method_with_numeric_values(self) -> None:
        """Test __lt__ semantics within the same IntEnum class."""
        assert NumericEnum.LOW < NumericEnum.MEDIUM
        assert NumericEnum.MEDIUM < NumericEnum.HIGH
        assert NumericEnum.LOW < NumericEnum.HIGH

        # Reflexivity
        assert not (NumericEnum.LOW < NumericEnum.LOW)
        assert not (NumericEnum.MEDIUM < NumericEnum.MEDIUM)
        assert not (NumericEnum.HIGH < NumericEnum.HIGH)

    def test_lt_method_cross_intenum_classes(self) -> None:
        """
        IntEnum compares across different IntEnum classes by underlying int values.
        This should not raise; it should compare like ints.
        """
        assert TestIntEnum.FIRST < NumericEnum.MEDIUM    # 1 < 5
        assert not (NumericEnum.LOW < TestIntEnum.FIRST)  # 1 < 1 -> False
        assert NumericEnum.HIGH > TestIntEnum.SECOND      # 10 > 2

    def test_lt_method_with_non_enum_types(self) -> None:
        """
        IntEnum compares to plain ints like an int; incompatible types raise TypeError.
        """
        # Allowed: compare to int
        assert NumericEnum.LOW < 5
        assert not (NumericEnum.HIGH < 5)

        # Not allowed: incompatible types
        with pytest.raises(TypeError):
            _ = NumericEnum.LOW < "string"  # type: ignore[operator]
        with pytest.raises(TypeError):
            _ = NumericEnum.LOW < None  # type: ignore[operator]
        with pytest.raises(TypeError):
            _ = NumericEnum.LOW < [1, 2, 3]  # type: ignore[operator]

    def test_enum_inheritance_properties(self) -> None:
        """Test that EnhancedIntEnum properly inherits from IntEnum and int."""
        assert issubclass(TestIntEnum, EnhancedIntEnum)
        assert isinstance(TestIntEnum.FIRST, TestIntEnum)
        assert isinstance(TestIntEnum.FIRST, EnhancedIntEnum)
        # IntEnum members behave as ints
        assert isinstance(TestIntEnum.FIRST, int)

        # Test that enum members have expected properties
        assert TestIntEnum.FIRST.name == "FIRST"
        assert TestIntEnum.FIRST.value == 1

    def test_enum_uniqueness(self) -> None:
        """Test that enum members are unique objects."""
        assert TestIntEnum.FIRST is TestIntEnum.FIRST
        assert TestIntEnum.FIRST is not TestIntEnum.SECOND  # type: ignore[comparison-overlap]

        # Creating enum with same value twice refers to same object
        first_ref1 = TestIntEnum(1)
        first_ref2 = TestIntEnum(1)
        assert first_ref1 is first_ref2
        assert first_ref1 is TestIntEnum.FIRST

    def test_method_return_types_are_correct(self) -> None:
        """Test that all methods return the expected types."""
        # names should return list[str]
        names = TestIntEnum.names()
        assert isinstance(names, list)
        assert all(isinstance(name, str) for name in names)

        # members should return list of members (instances)
        members = TestIntEnum.members()
        assert isinstance(members, list)
        assert all(isinstance(m, TestIntEnum) for m in members)

        # values should return list[int]
        vals = TestIntEnum.values()
        assert isinstance(vals, list)
        assert all(isinstance(v, int) for v in vals)

        # contains_value should return bool
        result = TestIntEnum.contains_value(1)
        assert isinstance(result, bool)

        # get_member should return T | None
        item = TestIntEnum.get_member(1)
        assert item is None or isinstance(item, TestIntEnum)

        # get_name should return str | None
        name = TestIntEnum.get_name(1)
        assert name is None or isinstance(name, str)

    def test_integration_with_standard_enum_features(self) -> None:
        """Test that EnhancedIntEnum works with standard Enum features."""
        # Test iteration
        enum_members = list(TestIntEnum)
        assert len(enum_members) == 5
        assert TestIntEnum.FIRST in enum_members

        # Test membership
        assert TestIntEnum.FIRST in TestIntEnum

        # Test string representation
        assert str(TestIntEnum.FIRST) == "TestIntEnum.FIRST"
        assert repr(TestIntEnum.FIRST) == "<TestIntEnum.FIRST: 1>"

    @pytest.mark.parametrize("enum_class", [TestIntEnum, SingleValueEnum])
    def test_all_methods_with_different_enum_classes(self, enum_class: Type[EnhancedIntEnum]) -> None:
        """Test methods work with different enum classes."""
        # Ensure methods don't crash with different enum types
        names = enum_class.names()
        vals = enum_class.values()

        assert isinstance(names, list)
        assert isinstance(vals, list)
        assert len(names) == len(vals)

        if names:  # If enum has members
            first_value = vals[0]
            assert enum_class.contains_value(first_value) is True
            assert enum_class.get_member(first_value) is not None
            assert enum_class.get_name(first_value) is not None

    def test_type_var_bound_constraint(self) -> None:
        """Test that type variable T is properly bound to EnhancedIntEnum."""
        item = TestIntEnum.get_member(1)
        if item is not None:
            assert isinstance(item, EnhancedIntEnum)
            assert isinstance(item, TestIntEnum)
