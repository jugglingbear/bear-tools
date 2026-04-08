# pylint: disable=R0903

import abc
from typing import Callable

from bear_tools import lumberjack
from bear_tools.misc_utils import do_nothing


class LoggingModBase(abc.ABC):
    """
    Abstract Base Class for logging mods
    """

    logger = lumberjack.Logger(default_color=lumberjack.PrintColor.GREEN)

    @abc.abstractmethod
    def handle_event(self, text: str, callback: Callable[..., None] = do_nothing) -> None:
        """
        Used by a CerealClient, this method is called for every line of logging that comes from a CerealServer

        :param text: The text sent from the CerealServer to a CerealClient that has this mod registered
        :param callback: An optional method to call
        """
