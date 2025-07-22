import time
from threading import Thread

from bear_tools import lumberjack

logger = lumberjack.Logger()


def wait_for_thread_to_start(thread: Thread, timeout_sec: float = 5.0, poll_interval: float = 0.01) -> bool:
    """
    Wait for a thread to start running.

    :param thread: The thread object to check.
    :param timeout_sec: Max time to wait (seconds).
    :param poll_interval: How often to check (seconds).
    :return: True if thread is alive within the timeout; False otherwise.
    """
    if not isinstance(thread, Thread):
        logger.error(f"thread is not a threading.Thread object. Actual type: {type(thread)}")
        return False

    start_time = time.perf_counter()
    while not thread.is_alive() and time.perf_counter() - start_time < timeout_sec:
        time.sleep(poll_interval)

    return thread.is_alive()
