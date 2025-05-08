from __future__ import annotations
import enum


class LogLevel(enum.Enum):
    """
    Supported logging levels

    Note:
        Messages are only logged if the user calls an API corresponding to a log level greater than or equal to the
        logger's set log level

    Example:
        If the logger's level is set to INFO:
            my_logger.noise('stuff')    # This would not be logged
            my_logger.debug('stuff')    # This would not be logged
            my_logger.info('stuff')     # This would be logged
            my_logger.warning('stuff')  # This would be logged
            my_logger.error('stuff')    # This would be logged
    """

    NOISE   = 0
    DEBUG   = 1
    INFO    = 2
    WARNING = 3
    ERROR   = 4
    SILENT  = 5

    def __lt__(self, other: LogLevel) -> bool:
        return self.value < other.value

    def __le__(self, other: LogLevel) -> bool:
        return self.value <= other.value

    def __gt__(self, other: LogLevel) -> bool:
        return self.value > other.value

    def __ge__(self, other: LogLevel) -> bool:
        return self.value >= other.value
