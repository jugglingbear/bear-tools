"""
Dictionary utility functions for safe key lookups and nested access.

This module provides utilities for safely accessing dictionary values with
improved error handling, type safety, and support for nested key paths.
"""

from typing import Any, Hashable, Optional, Sequence, TypeVar, Union, cast

T = TypeVar('T')


def lookup(
    key: Hashable,
    source: dict[Any, Any],
    strict: bool = True,
    default: Optional[T] = None
) -> Any:
    """
    Safely lookup a value associated with a key in a dictionary.

    Examples:
        >>> data = {'name': 'John', 'age': 30}
        >>> lookup('name', data)
        'John'
        >>> lookup('height', data, strict=False)
        None
        >>> lookup('height', data, strict=False, default='unknown')
        'unknown'

    This function provides a safe way to access dictionary values with better
    error handling and optional default value support.

    :param key: The key whose corresponding value is sought from the dict.
        Can be any hashable type (str, int, tuple, etc.)
    :param source: The source dictionary to look in
    :param strict: If True, raises KeyError if key isn't found; otherwise returns the default value if key isn't found
    :param default: The value to return if the key is not found and strict=False.
        Defaults to None
    :return: The value associated with the key if it exists;
        otherwise the default value (when strict=False) or raises KeyError (when strict=True)
    :raises TypeError: If source is not a dictionary
    :raises KeyError: If operating in strict mode and key is not found in the dict
    """
    if not isinstance(source, dict):
        raise TypeError(
            f"Expected source to be a dict, got {type(source).__name__}"
        )

    try:
        return source[key]
    except KeyError as error:
        if strict:
            raise KeyError(
                f"Key '{key}' not found in dictionary with keys: {list(source.keys())}"
            ) from error
        return default


def nested_lookup(
    key_path: Union[str, Sequence[Hashable]],
    source: dict[Any, Any],
    separator: str = ".",
    strict: bool = True,
    default: Optional[T] = None
) -> Any:
    """
    Safely lookup a value in a nested dictionary using a key path.

    Examples:
        >>> data = {'user': {'profile': {'name': 'John', 'age': 30}}}
        >>> nested_lookup('user.profile.name', data)
        'John'
        >>> nested_lookup(['user', 'profile', 'age'], data)
        30
        >>> nested_lookup('user.profile.height', data, strict=False)
        None
        >>> nested_lookup('user.settings.theme', data, strict=False, default='dark')
        'dark'

    This function allows accessing deeply nested dictionary values using either
    a dot-separated string path or a sequence of keys.

    :param key_path: Either a string with keys separated by the separator, or a
        sequence of keys to traverse the nested dictionary
    :param source: The source dictionary to look in
    :param separator: The separator to use when splitting string key paths.
        Defaults to "."
    :param strict: If True, raises KeyError if any key in the path isn't found;
        otherwise returns the default value
    :param default: The value to return if any key in the path is not found and
        strict=False. Defaults to None
    :return: The value at the end of the key path if it exists, otherwise the
        default value (when strict=False) or raises KeyError (when strict=True)
    :raises TypeError: If source is not a dictionary or if intermediate values
        are not dictionaries when expected
    :raises KeyError: If operating in strict mode and any key in the path is not found
    """
    if not isinstance(source, dict):
        raise TypeError(
            f"Expected source to be a dict, got {type(source).__name__}"
        )

    # Convert string path to sequence of keys
    keys: list[Hashable]
    if isinstance(key_path, str):
        keys = cast(list[Hashable], key_path.split(separator) if key_path else [])
    else:
        keys = list(key_path)

    if not keys:
        return source

    current = source
    for i, key in enumerate(keys):
        try:
            if not isinstance(current, dict):
                if strict:
                    raise TypeError(
                        f"Expected dict at path '{separator.join(str(k) for k in keys[:i])}', "
                        f"got {type(current).__name__}"
                    )
                return default
            current = current[key]
        except KeyError as error:
            if strict:
                partial_path = separator.join(str(k) for k in keys[:i + 1])
                available_keys = list(current.keys()) if isinstance(current, dict) else []
                raise KeyError(
                    f"Key '{key}' not found at path '{partial_path}'. "
                    f"Available keys: {available_keys}"
                ) from error
            return default

    return current


def safe_get(
    source: dict[Any, Any],
    key: Hashable,
    default: Optional[T] = None
) -> Union[Any, T]:
    """
    Get a value from a dictionary with a default fallback.

    Examples:
        >>> data = {'name': 'John', 'age': 30}
        >>> safe_get(data, 'name')
        'John'
        >>> safe_get(data, 'height', 'unknown')
        'unknown'

    This is a convenience function equivalent to dict.get() but with better
    type hints and consistent interface with other functions in this module.

    :param source: The source dictionary to look in
    :param key: The key to look up
    :param default: The value to return if the key is not found. Defaults to None
    :return: The value associated with the key if it exists, otherwise the default value
    :raises TypeError: If source is not a dictionary
    """
    if not isinstance(source, dict):
        raise TypeError(
            f"Expected source to be a dict, got {type(source).__name__}"
        )

    return source.get(key, default)
