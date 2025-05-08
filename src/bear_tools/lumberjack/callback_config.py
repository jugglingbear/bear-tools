from dataclasses import dataclass
from typing import Callable


@dataclass
class CallbackConfig:
    """
    Holds all necessary information about a logging callback method
    """

    callback:       Callable[[str], None]
    add_timestamps: bool
    add_caller:     bool
