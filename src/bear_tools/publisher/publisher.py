import abc
import threading
from typing import Any

from bear_tools import lumberjack
from bear_tools.publisher.listener import Listener

logger = lumberjack.Logger()


class Publisher(abc.ABC, threading.Thread):
    """
    <<< Abstract Base Class >>>

    Publisher class that listens for <some kind of event> and notifies registered listeners/subscribers about the
    events when the happen
    """

    def __init__(self, nickname: str = 'Publisher'):
        """
        Initializer

        :param nickname: How the publisher is referred to in logging (optional)
        """

        super(Publisher, self).__init__()
        self.daemon = True
        self.__stop_thread = False
        self.__lock = threading.Lock()

        self.nickname = nickname
        self.__listeners: list[Listener] = []


    def register_listener(self, listener: Listener) -> None:
        """
        Register a listener to be notified when events occur

        :param listener: Listener to notify when events occur
        """

        with self.__lock:
            logger.debug(f'[{self.nickname}] Registering new listener: {listener.nickname}')
            self.__listeners.append(listener)


    def stop(self) -> None:
        """
        Signal to the main thread loop that the thread should stop
        """

        logger.debug(f'[{self.nickname}] Signaling thread to stop')
        self.__stop_thread = True


    def unregister_listener(self, listener: Listener) -> None:
        """
        Unregister a listener

        :param listener: A previously-registered listener
        """

        with self.__lock:
            logger.debug(f'[{self.nickname}] Unregistering listener: {listener.nickname}')
            self.__listeners = [item for item in self.__listeners if item != listener]


    def notify_listeners(self, event: Any) -> None:
        """
        Notify listeners that an event occurred

        :param event: An object representing the event that occurred
        """

        with self.__lock:
            logger.debug(f'[{self.nickname}] Notifying {len(self.__listeners)} listeners about new event: {event}')
            for listener in self.__listeners:
                logger.debug(f'[{self.nickname}] Sending event to {listener.nickname}: {event}')
                listener.handle_event(event)


    def run(self) -> None:
        """
        Main thread loop
        """

        logger.debug(f'[{self.nickname}] Starting main thread loop')
        while True:
            if self.__stop_thread:
                break

            self.main_thread_loop_body()

        logger.debug(f'[{self.nickname}] Main thread loop stopped')


    @abc.abstractmethod
    def main_thread_loop_body(self) -> None:
        """
        Body of main thread loop that listens for events and calls notify_listeners when one is observed
        """

        pass
