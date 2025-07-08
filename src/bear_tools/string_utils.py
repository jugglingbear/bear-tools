import re
from copy import deepcopy

from bear_tools.lumberjack import Logger, LogLevel

logger = Logger(LogLevel.INFO)


def bytearray2str(data: bytearray | bytes | str | None, simple_hex: bool = False) -> str | None:
    """
    Convert a bytearray into a human-readable equivalent hex string

    :param data: An array of bytes
    :param simple_hex: If True, return hex of the form 'XXXXXX'; otherwise, return hex of the form '<0xXX 0xXX 0xXX>'
    :return: A nicely-formatted dump of the individuals bytes in a bytearray or None if there's an error
    """

    if data is None:
        return None
    if isinstance(data, list) and not data:
        return '<no data>'

    if isinstance(data, bytearray):
        data_bytes = data
    elif isinstance(data, bytes):
        data_bytes = bytearray(data)
    elif isinstance(data, str):
        data_bytes = bytearray(data, encoding='utf-8')
    else:
        # On macOS using the bleak package, notifications can come back as Foundation._NSInlineData, which can be
        # directly typecast to a bytearray
        try:
            data_bytes = bytearray(data)
        except Exception as error:
            raise TypeError(f'Failed to convert data ({data}, type: {type(data)}) to a bytearray') from error

    if simple_hex:
        return ''.join([f'{byte:>02X}' for byte in data_bytes])
    return ':'.join([f'{byte:>02X}' for byte in data_bytes])


def get_aligned_text(text: list[list[str]], extra_padding: int = 2) -> list[list[str]]:
    """
    Update a 2D list of strings such that each column has the same width for aesthetic printing

    :param text: Raw text to align
    :param extra_padding: How many extra spaces of padding to add to each row
    :return: The same 2D list of strings with each cell appended with whitespace to make it match the max col width
    :raises ValueError: If extra_padding is not a non-negative integer
    """

    if isinstance(extra_padding, int) and extra_padding < 0:
        raise ValueError(f'Expected: extra_padding is a non-negative integer, got {extra_padding}')
    if not text:
        return []
    

    padded_text: list[list[str]] = deepcopy(text)
    col_widths: list[int] = [max(len(_row[_col]) for _row in text) + extra_padding for _col in range(len(text[0]))]

    for row in padded_text:
        for col_index, cell in enumerate(row):
            if len(padded_text) == 1:
                row[col_index] = f'{cell:<{max(col_widths)}}'
            else:
                row[col_index] = f'{cell:<{col_widths[col_index]}}'

    return padded_text


def remove_control_chars(text: str) -> str:
    """
    Remove all control characters from a string

    Warning: This removes TAB and CRLF too

    :param text: Text to strip of control characters
    :return: The same text minus all control characters
    """

    # Create a translation table with control characters mapped to None
    control_chars = ''.join(map(chr, range(0, 32))) + chr(127)
    translation_table = str.maketrans('', '', control_chars)
    return text.translate(translation_table)
