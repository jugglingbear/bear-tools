"""
A module containing utility functions for working with YAML files/data
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

from bear_tools import lumberjack
from ruamel import yaml
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.error import YAMLError

logger = lumberjack.Logger()


def get_nested(data: CommentedMap, *keys: str) -> Any | None:
    """
    Get data from a nested dictionary-style YAML object

    Example:
        Given: {'key1': {'key2': {'key3': 12345}}}
        If *keys == ('key1', 'key2', 'key3')
        The final result value will be 12345

    :param data: Contains YAML data
    :param keys: Keys corresponding to a value that the user wants to extract from hierarchical data (see example above)
    :return: The data from the given set of keys if found; None otherwise
    """

    i: int = 0
    node = data

    try:
        for i, _key in enumerate(keys):
            node = node.get(_key)
        return node
    except AttributeError as error:
        logger.error(f'Attribute Error: Cannot access "{keys[i]}" from keys {keys} in data:\n{data}. Error: "{error}"')
        return None
    except KeyError as error:
        logger.error(f'Key "{keys[i]}" not found in keys: {keys}. Error: "{error}"')
        return None


def get_string(data: yaml.YAML) -> str:
    """
    Convert a YAML object into a string

    Includes all whitespace formatting and comments in the YAML file

    :param data: Contains YAML data
    """

    sio = StringIO()
    y = yaml.YAML()
    y.dump(data, sio)
    return sio.getvalue()


def load(path: Path) -> CommentedMap | None:
    """
    Load a YAML file

    :param path: Path to YAML file
    :return: YAML object if load was successful; None otherwise
    """

    y = yaml.YAML()
    try:
        with open(path, encoding='utf-8') as _f:
            data: CommentedMap = y.load(_f)
    except IOError as error:
        logger.error(f'Failed to load "{path}". Error: "{error}"')
        return None
    except YAMLError as error:
        logger.error(f'Failed to load "{path}" into YAML object. Error: "{error}"')
        return None

    return data


def save(path: Path, data: CommentedMap) -> bool:
    """
    Save YAML data to a file

    :param path: Where to save the file
    :param data: The data to savea
    :return: True if save was successful; False otherwise
    """

    y = yaml.YAML()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            y.dump(data, f)
    except IOError as error:
        logger.error(f'Failed to open "{path}" for writing. Error: "{error}"')
        return False
    except YAMLError as error:
        logger.error(f'Failed to dump YAML data to "{path}". Error: "{error}"')
        return False
    return True
