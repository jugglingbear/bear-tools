"""
A module containing utility functions for working with YAML files/data
"""

from io import StringIO
from pathlib import Path
from typing import Any

from ruamel import yaml
from ruamel.yaml.error import YAMLError
from ruamel.yaml.comments import CommentedMap

from bear_tools import lumberjack
logger = lumberjack.Logger()


def get_nested(data: CommentedMap, *keys: dict[str, Any]) -> Any | None:
    """
    Get data from a nested dictionary-style YAML object

    :param data: Contains YAML data
    :param keys: A set of nested keys from which to get a value (e.g. {'key1': {'key2': {'key3': 12345}}})
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
        with open(path) as _f:
            data: CommentedMap = y.load(_f)
    except IOError as error:
        logger.error(f'Failed to load "{path}". Error: "{error}"')
        return None
    except YAMLError as error:
        logger.error(f'Failed to load "{path}" into YAML object. Error: "{error}"')
        return None

    return data
