# pylint: disable=W0613
# pylint: disable=R0913,R0917

"""
Miscellaneous Utilities
"""

import math
import operator
import time
from functools import reduce
from typing import Any, Callable, Iterable, Literal, TypeVar

from bear_tools import lumberjack

T = TypeVar('T')
OPERATOR_SYMBOLS: dict[Callable[[Any, Any], bool], str] = {
    operator.eq: '==',
    operator.ne: '!=',
    operator.lt: '<',
    operator.le: '<=',
    operator.gt: '>',
    operator.ge: '>='
}
logger = lumberjack.Logger()



def do_nothing(*args: object, **kwargs: object) -> None:
    """Function that does absolutely nothing. Useful as a default callback value"""


def get_number_of_bytes(value: int) -> int:
    """
    Get the number of bytes required to represent a given value

    :param value: Any numerical value
    """

    return max(1, int(math.ceil(value.bit_length() / 8.)))


def int2bytearray(value: int, byteorder: Literal['big', 'little'] = 'big') -> bytearray:
    """
    Split an integer value into an ordered set of bytes stored in a bytearray

    :param value: An unsigned integer value
    :param byteorder: The byte order to use (optional)
    :return: A bytearray that contains bytes that, when put in Big Endian order, convert back to the original value
    """

    byte_count: int = get_number_of_bytes(value)
    bytes_value = value.to_bytes(byte_count, byteorder=byteorder)
    return bytearray(bytes_value)


def is_subsequence(a: Iterable[T], b: Iterable[T]) -> bool:
    """
    Determine if a is a subsequence (ordered subset) of b

    :param a: A list/tuple/etc that is iterable
    :param b: A list/tuple/etc that is iterable
    :return: True if a is a subsequence of b; False otherwise
    """

    iterator = iter(b)
    return all(item in iterator for item in a)


def wait_for_nested_property(
    obj: Any,
    property_name_list: list[str],
    operator_method: Callable[[Any, Any], bool] = operator.eq,
    expected_value: object = None,
    timeout: float = 10.0,
    cooldown: float = 0.5
) -> bool:
    """
    Repeatedly check the value of a property at the end of a "property chain" until it satisfies a given requirement

    For Example:
        Given:
        - ClassA has property_a, which returns a ClassB
        - ClassB has property_b, which returns <some value>
        - We have an instance of ClassA, called objectA

        Want:
        - The value of property_b

        Solution:
        - objectA.property_a.property_b

    :param obj: Any object that contains a @property
    :param property_name_list: An ordered list of property names to drill down
    :param expected_value: The anticipated value of the property at the end of the chain
    :param operator_method: One of the mathematical operator methods from the operator package (e.g. operator.eq)
    :param timeout: The maximum amount of time to spend checking the property value before giving up
    :param cooldown: How long, in seconds, to wait between checking the property value
    :return: True if the property met the expected value within the time limit; False otherwise
    """

    if timeout <= 0 or cooldown <= 0:
        raise ValueError(f'cooldown_time and timeout must be > 0. cooldown_time: {cooldown}, timeout: {timeout}')

    if not property_name_list:
        raise ValueError('property_name_list cannot be empty')

    def resolve_nested(obj: Any) -> Any:
        """Resolve the property chain, handling None values gracefully"""
        try:
            return reduce(getattr, property_name_list, obj)
        except AttributeError as e:
            logger.error(f'Property chain {".".join(property_name_list)} failed: {e}')
            raise

    start_time = time.perf_counter()
    property_value = None
    while (elapsed := time.perf_counter() - start_time) <= timeout:
        try:
            property_value = resolve_nested(obj)
            logger.debug(f'expected_value: {expected_value}, property_value: {property_value}')

            if operator_method(property_value, expected_value):
                return True

        except AttributeError:
            # Property doesn't exist, no point in continuing
            return False

        time.sleep(cooldown)

    operator_symbol = OPERATOR_SYMBOLS.get(operator_method, str(operator_method))
    property_chain = ".".join(property_name_list)
    logger.error(
        f'Timeout after {elapsed:.2f}s: {property_chain} {operator_symbol} {expected_value} '
        f'(Last value: {property_value})'
    )
    return False


def wait_for_property(
    instance: Any,
    property_name: str,
    operator_method: Callable[[Any, Any], bool] = operator.eq,
    expected_value: object = None,
    timeout: float = 10.0,
    cooldown_time: float = 0.5
) -> bool:
    """
    Repeatedly check the value of a property until it satisfies an expected value with a given mathematical operator

    :param instance: Any object that contains a @property
    :param property_name: The name of the @property to check
    :param operator_method: One of the mathematical operator methods from the operator package (e.g. operator.eq)
    :param expected_value: The anticipated value of the @property
    :param timeout: The maximum amount of time to spend checking the property value before giving up
    :param cooldown_time: How long, in seconds, to wait between checking the property value
    :return: True if the property met the expected value within the time limit; False otherwise
    """

    return wait_for_nested_property(instance, [property_name], operator_method, expected_value, timeout, cooldown_time)
