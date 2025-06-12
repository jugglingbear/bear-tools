from typing import Any

from bear_tools import lumberjack
from bear_tools.publisher import Listener

cyan = lumberjack.PrintColor.CYAN
logger = lumberjack.Logger()


class NewspaperCustomer(Listener):
    """
    A customer who subscribes to receive newspapers
    """

    def __init__(self, name: str, address: str, city: str, state: str, zipcode: str):
        """
        Initializer

        :param name: Customer name
        :param address: Customer's address
        :param city: Customer's city of residence
        :param state: Customer's state of residence
        :param zipcode: Customer's zipcode
        """

        super().__init__(name)
        self.name:    str = name
        self.address: str = address
        self.city:    str = city
        self.state:   str = state
        self.zipcode: str = zipcode


    def handle_event(self, event: Any) -> None:
        """
        Handle event notification from the publisher

        :param event: An object containing information about the event
        """

        logger.info(f'[{self.name}] Received newspaper: {event}', color=cyan)
