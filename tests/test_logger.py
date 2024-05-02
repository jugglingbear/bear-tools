import itertools
import pytest
from bear_tools.lumberjack import Logger, LogLevel, PrintColor

test_text: str = 'test'
test_symbols: list[str] = ['.', '..', '...']


def test_Logger_log_level_basic() -> None:
    """
    Verify that loggers can be instantiated at all log levels
    """

    for _log_level in LogLevel:
        try:
            logger = Logger(_log_level)
        except:
            pytest.fail(f'Failed to instantiate Logger with log level: {_log_level}')
        assert logger.log_level == _log_level, f'Expected log level: {_log_level}, actual: {logger.log_level}'


def test_Logger_set_log_level() -> None:
    """
    Verify that the log level can be set to good values and cannot be set to bad values
    """

    logger = Logger()

    # Happy path
    for _log_level in LogLevel:
        try:
            logger.log_level = _log_level
        except:
            pytest.fail(f'Failed to set log level to {_log_level}')


    # Unhappy path
    expected = LogLevel.INFO
    for _log_level in ('cheese', 1, 1.23, {'key':'value'}, (1, 2, 3), [1, 2, 3]):
        logger.log_level = _log_level  # type: ignore
        assert logger.log_level == expected, f'Expected log level: {expected}, actual: {logger.log_level}'


def test_Logger_banner() -> None:
    """
    Verify that there are no problems calling the banner API
    """

    logger = Logger()
    for _color in PrintColor:
        for _symbol in test_symbols:
            try:
                logger.banner(text=test_text, color=_color, symbol=_symbol)
                logger.banner(text=test_text, color=_color.value, symbol=_symbol)
            except:
                pytest.fail(f'Failed to log banner with text: "{test_text}", color: {_color}, symbol: "{_symbol}"')


def test_Logger_noise() -> None:
    """
    Verify that there are no problems calling the noise API
    """

    logger = Logger()
    for _color in PrintColor:
        for _symbol in test_symbols:
            try:
                logger.noise(text=test_text, color=None)
                logger.noise(text=test_text, color=_color)
                logger.noise(text=test_text, color=_color.value)
            except:
                pytest.fail(f'Failed to log noise with text: "{test_text}", color: {_color}, symbol: "{_symbol}"')


def test_Logger_debug() -> None:
    """
    Verify that there are no problems calling the debug API
    """

    logger = Logger()
    for _color in PrintColor:
        for _symbol in test_symbols:
            try:
                logger.debug(text=test_text, color=None)
                logger.debug(text=test_text, color=_color)
                logger.debug(text=test_text, color=_color.value)
            except:
                pytest.fail(f'Failed to log debug with text: "{test_text}", color: {_color}, symbol: "{_symbol}"')


def test_Logger_info() -> None:
    """
    Verify that there are no problems calling the info API
    """

    logger = Logger()
    for _color in PrintColor:
        for _symbol in test_symbols:
            try:
                logger.info(text=test_text, color=None)
                logger.info(text=test_text, color=_color)
                logger.info(text=test_text, color=_color.value)
            except:
                pytest.fail(f'Failed to log info with text: "{test_text}", color: {_color}, symbol: "{_symbol}"')


def test_Logger_warning() -> None:
    """
    Verify that there are no problems calling the warning API
    """

    logger = Logger()
    for _color in PrintColor:
        for _symbol in test_symbols:
            try:
                logger.warning(text=test_text, color=None)
                logger.warning(text=test_text, color=_color)
                logger.warning(text=test_text, color=_color.value)
            except:
                pytest.fail(f'Failed to log warning with text: "{test_text}", color: {_color}, symbol: "{_symbol}"')


def test_Logger_error() -> None:
    """
    Verify that there are no problems calling the error API
    """

    logger = Logger()
    for _color in PrintColor:
        for _symbol in test_symbols:
            try:
                logger.error(text=test_text, color=None)
                logger.error(text=test_text, color=_color)
                logger.error(text=test_text, color=_color.value)
            except:
                pytest.fail(f'Failed to log error with text: "{test_text}", color: {_color}, symbol: "{_symbol}"')


@pytest.mark.parametrize('log_level, add_timestamps, add_caller', list(itertools.product(
    list(LogLevel), (True, False), (True, False)
)))
def test_Logger_register_and_unregister_callback(log_level: LogLevel, add_timestamps: bool, add_caller: bool) -> None:
    """
    Verify that callbacks registered at specific levels get called
    """

    def callback(text: str) -> None:
        print(f'Callback triggered. text: "{text}"')
        callback_data['value'] = True

    logger = Logger(log_level=log_level)

    # Verify that the callback is triggered when registered
    logger.register_callback(log_level, callback, add_timestamps, add_caller)
    callback_data: dict = {}
    if log_level != LogLevel.SILENT:
        api_name = str(log_level.name).lower()
        api = getattr(logger, api_name)
        api(f'Calling logger.{api_name}')  # This should trigger the callback
        callback_triggered: bool = callback_data.get('value', False)
        assert callback_triggered, f'logger.{api_name} failed to trigger callback'

    logger.unregister_callback(log_level=log_level, callback=callback)
    callback_data = {}

    # Verify that the callback is not triggered when not registered
    if log_level != LogLevel.SILENT:
        api_name = str(log_level.name).lower()
        api = getattr(logger, api_name)
        api(f'Calling logger.{api_name}')  # This should trigger the callback
        callback_triggered: bool = callback_data.get('value', False)
        assert not callback_triggered, f'logger.{api_name} triggered the callback after unregistering'

