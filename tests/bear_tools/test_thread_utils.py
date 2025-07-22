# flake8: noqa: E501
# pylint: disable=C0301

"""
Unit tests for bear_tools/thread_utils.py
"""

import time
from threading import Thread
from typing import Any
from unittest.mock import MagicMock, patch

from bear_tools import thread_utils


def _dummy_worker(delay: float = 0.05) -> None:
    """A simple worker function that sleeps for a bit"""
    time.sleep(delay)


def test_wait_for_thread_to_start_success() -> None:
    """Verify that wait_for_thread_to_start returns True when a thread starts within the timeout"""
    thread: Thread = Thread(target=_dummy_worker)
    thread.start()
    result: bool = thread_utils.wait_for_thread_to_start(thread, timeout_sec=1.0, poll_interval=0.01)
    thread.join()
    assert result is True


def test_wait_for_thread_to_start_timeout() -> None:
    """Verify that wait_for_thread_to_start returns False when the thread never starts"""
    thread: Thread = Thread(target=_dummy_worker)
    # Do NOT call thread.start(), so it never becomes alive
    result: bool = thread_utils.wait_for_thread_to_start(thread, timeout_sec=0.1, poll_interval=0.01)
    assert result is False


@patch.object(thread_utils.logger, "error")
def test_wait_for_thread_to_start_invalid_type(mock_logger_error: MagicMock) -> None:
    """Verify that wait_for_thread_to_start logs an error and returns False when given a non-Thread object"""
    result: bool = thread_utils.wait_for_thread_to_start("not_a_thread", timeout_sec=0.1)  # type: ignore[arg-type]
    assert result is False
    mock_logger_error.assert_called_once()
    args: tuple[Any, ...] = mock_logger_error.call_args[0]
    assert "thread is not a threading.Thread object" in args[0]


def test_wait_for_thread_to_start_with_delayed_start() -> None:
    """Verify that wait_for_thread_to_start handles a thread that starts after a short delay"""
    def delayed_start() -> None:
        time.sleep(0.05)
    thread: Thread = Thread(target=delayed_start)
    thread.start()
    result: bool = thread_utils.wait_for_thread_to_start(thread, timeout_sec=1.0, poll_interval=0.01)
    thread.join()
    assert result is True
