import abc
from typing import Any


class Listener(abc.ABC):
    """
    <<< Abstract Base Class >>>

    Listener/subscriber class. Can register with the Publisher to be notified about events when they happen
    """

    def __init__(self, nickname: str = 'Listener'):
        """
        Initializer

        :param nickname: How the listener is referred to in logging (optional)
        """

        self.nickname = nickname


    @abc.abstractmethod
    def handle_event(self, event: Any) -> None:
        """
        Handle event notification from the publisher

        :param event: An object containing information about the event
        """

        pass
