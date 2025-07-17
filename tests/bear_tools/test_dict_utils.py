# flake8: noqa: E501
# pylint: disable=C0301,C0116

"""
Unit tests for dictionary utility functions: lookup, nested_lookup, and safe_get.
"""

from typing import Any, cast

import pytest

from bear_tools.dict_utils import lookup, nested_lookup, safe_get

# -------------------------
# Tests for lookup()
# -------------------------

def test_lookup_existing_key_strict() -> None:
    data: dict[str, Any] = {"name": "John", "age": 30}
    assert lookup("name", data) == "John"
    assert lookup("age", data) == 30


def test_lookup_missing_key_non_strict_default_none() -> None:
    data: dict[str, Any] = {"name": "John"}
    assert lookup("height", data, strict=False) is None


def test_lookup_missing_key_non_strict_with_default() -> None:
    data: dict[str, Any] = {"name": "John"}
    assert lookup("height", data, strict=False, default="unknown") == "unknown"


def test_lookup_missing_key_strict_raises() -> None:
    data: dict[str, Any] = {"name": "John"}
    with pytest.raises(KeyError, match="Key 'height' not found"):
        lookup("height", data, strict=True)


def test_lookup_invalid_source_type() -> None:
    with pytest.raises(TypeError, match="Expected source to be a dict"):
        lookup("key", cast(Any, ["not", "a", "dict"]))


# -------------------------
# Tests for nested_lookup()
# -------------------------

def test_nested_lookup_string_path_existing() -> None:
    data: dict[str, Any] = {"user": {"profile": {"name": "John", "age": 30}}}
    assert nested_lookup("user.profile.name", data) == "John"
    assert nested_lookup("user.profile.age", data) == 30


def test_nested_lookup_list_path_existing() -> None:
    data: dict[str, Any] = {"user": {"profile": {"name": "John"}}}
    assert nested_lookup(["user", "profile", "name"], data) == "John"


def test_nested_lookup_missing_key_non_strict() -> None:
    data: dict[str, Any] = {"user": {"profile": {"name": "John"}}}
    assert nested_lookup("user.profile.height", data, strict=False) is None


def test_nested_lookup_missing_key_non_strict_with_default() -> None:
    data: dict[str, Any] = {"user": {"profile": {"name": "John"}}}
    assert nested_lookup("user.profile.height", data, strict=False, default="unknown") == "unknown"


def test_nested_lookup_missing_key_strict_raises() -> None:
    data: dict[str, Any] = {"user": {"profile": {"name": "John"}}}
    with pytest.raises(KeyError, match="Key 'height' not found"):
        nested_lookup("user.profile.height", data, strict=True)


def test_nested_lookup_invalid_source_type() -> None:
    with pytest.raises(TypeError, match="Expected source to be a dict"):
        nested_lookup("user.profile.name", cast(Any, ["not", "a", "dict"]))


def test_nested_lookup_intermediate_not_dict_strict_raises() -> None:
    data: dict[str, Any] = {"user": {"profile": "not_a_dict"}}
    with pytest.raises(TypeError, match="Expected dict at path 'user.profile'"):
        nested_lookup("user.profile.name", data, strict=True)


def test_nested_lookup_intermediate_not_dict_non_strict() -> None:
    data: dict[str, Any] = {"user": {"profile": "not_a_dict"}}
    assert nested_lookup("user.profile.name", data, strict=False, default="fallback") == "fallback"


def test_nested_lookup_empty_path_returns_source() -> None:
    data: dict[str, Any] = {"a": 1}
    assert nested_lookup("", data) == data
    assert nested_lookup([], data) == data


def test_nested_lookup_custom_separator() -> None:
    data: dict[str, Any] = {"user": {"profile": {"name": "John"}}}
    assert nested_lookup("user|profile|name", data, separator="|") == "John"


# -------------------------
# Tests for safe_get()
# -------------------------

def test_safe_get_existing_key() -> None:
    data: dict[str, Any] = {"name": "John"}
    assert safe_get(data, "name") == "John"


def test_safe_get_missing_key_default_none() -> None:
    data: dict[str, Any] = {"name": "John"}
    assert safe_get(data, "age") is None


def test_safe_get_missing_key_with_default() -> None:
    data: dict[str, Any] = {"name": "John"}
    assert safe_get(data, "age", default="unknown") == "unknown"


def test_safe_get_invalid_source_type() -> None:
    with pytest.raises(TypeError, match="Expected source to be a dict"):
        safe_get(cast(Any, ["not", "a", "dict"]), "key")
