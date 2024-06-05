from datetime import datetime
import time

from bear_tools.publisher import Publisher
from bear_tools import lumberjack

green = lumberjack.PrintColor.GREEN
logger = lumberjack.Logger()


class NewspaperPublisher(Publisher):
    """
    An entity who regularly publishes newspaper and sends them to customers
    """

    def __init__(self, name: str, publish_frequency: float):
        """
        Initializer

        :param name: The name of the newspaper organization
        :param publish_frequency:  How often (seconds) to publish a newspaper
        """

        super().__init__(name)
        self.name:              str   = name
        self.publish_frequency: float = publish_frequency


    def main_thread_loop_body(self) -> None:
        """
        Body of main thread loop that listens for events and calls notify_listeners when one is observed
        """

        now = datetime.now()
        if now.second % self.publish_frequency == 0:
            newspaper: str = f'📰📰📰 Hot off the press! The current time is {now} 📰📰📰'
            logger.info(f'[{self.name}] Sending newspaper to all customers: {newspaper}', color=green)
            self.notify_listeners(newspaper)
            time.sleep(1.0)  # Do not send multiple notifications per second

