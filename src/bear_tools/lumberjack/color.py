
"""
Tools to print in color!
"""

import enum
import sys
from typing import TextIO


class PrintColor(enum.Enum):
    """
    High intensity colors (the "regular" ones are '\033[3Xm' (for X in [0..7]) but are too dark)
    Use hexdump -C $(tput setaf <NUMBER>) to see codes

    Source:
        https://misc.flogisoft.com/bash/tip_colors_and_formatting
    """

    WHITE  = '\033[97m'
    RED    = '\033[91m'
    ORANGE = '\033[38;5;208m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    CYAN   = '\033[96m'
    BLUE   = '\033[94m'
    PURPLE = '\033[95m'
    BROWN  = '\033[38;5;94m'
    BLACK  = '\033[90m'

    # Turn off special coloring
    COLOR_OFF = '\033[0m'


def print_color(message: str, color: PrintColor | str, path: TextIO = sys.stdout, end: str = '\n') -> None:
    """
    Print to stdout in a specific color

    :param message: Message to print
    :param color: Any PrintColor.XXX value
    :param file: Where to send the text
    :param end: Optional text suffix
    """

    color = color.value if isinstance(color, PrintColor) else color
    print(f'{color}{message}{PrintColor.COLOR_OFF.value}', file=path, end=end)


def get_color_str(message: str, color: PrintColor | str) -> str:
    """
    Get string representation onf a colorized message

    :param message: String message
    :param color: Any PrintColor.XXX value
    :return: String with control characters that cause it to be colorized when printed to stdout
    """

    color = color.value if isinstance(color, PrintColor) else color
    return f'{color}{message}{PrintColor.COLOR_OFF.value}'
