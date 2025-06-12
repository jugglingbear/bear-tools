# pylint: disable=W0718,C0103

import pytest

from bear_tools.lumberjack import CallbackConfig


def test_CallbackConfig() -> None:
    """Test basics of the CallbackConfig class"""
    def callback(_: str) -> None:
        pass

    for _add_timestamps in (True, False):
        for _add_caller in (True, False):
            try:
                _ = CallbackConfig(callback=callback, add_timestamps=_add_timestamps, add_caller=_add_caller)
            except Exception:
                pytest.fail()
