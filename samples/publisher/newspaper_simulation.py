"""
Example of a newspaper system that uses the publisher subpackage
"""

import time

from bear_tools import lumberjack
from newspaper_publisher import NewspaperPublisher
from newspaper_customer import NewspaperCustomer

logger = lumberjack.Logger()


def main():
    publish_frequency: float = 5.0  # How often will the publisher publish something
    publisher = NewspaperPublisher('The Clock Times', publish_frequency)
    customers: list[NewspaperCustomer] = [
        NewspaperCustomer('Guy Incognito', '123 Sesame St', 'Anytown', 'WI', '12345'),
        NewspaperCustomer('J. Doe', '743 Evergreen Ter.', 'Springfield', 'VT', '05156'),
        NewspaperCustomer('S. Holmes', '221B Baker St.', 'New York', 'NY', '10001'),
    ]

    for _customer in customers:
        publisher.register_listener(_customer)

    logger.info(f'Starting up the simulator. The publisher will publish content every {publish_frequency} seconds')
    publisher.run()
    simulation_duration: float = 30.0  # seconds
    start_time: float = time.perf_counter()
    while time.perf_counter() - start_time <= simulation_duration:
        pass
    publisher.stop()


if __name__ == '__main__':
    main()

