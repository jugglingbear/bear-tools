from bear_tools.lumberjack import LogLevel


def test_LogLevel() -> None:
    # Subtest: Make sure all values are ints
    for _enum in LogLevel:
        assert isinstance(_enum.value, int), f"LogLevel contains non-int value: {_enum} (value: {_enum.value})"

    # Subtest: Make sure comparison operators are working as expected
    subtests = {
        LogLevel.NOISE: [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR],
        LogLevel.DEBUG: [LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR],
        LogLevel.INFO: [LogLevel.WARNING, LogLevel.ERROR],
        LogLevel.WARNING: [LogLevel.ERROR],
    }

    for log_level, higher_log_levels in subtests.items():
        for higher_log_level in higher_log_levels:
            assert log_level < higher_log_level
            assert log_level <= higher_log_level
            assert higher_log_level > log_level
            assert higher_log_level >= log_level
            assert log_level != higher_log_level
