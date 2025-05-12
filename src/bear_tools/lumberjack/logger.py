from __future__ import annotations
import datetime
import inspect
import io
from pathlib import Path
import sys
import time
from typing import Callable, TextIO

from bear_tools.lumberjack import CallbackConfig, LogLevel, print_color, PrintColor


class Logger:
    """
    The main logging class
    """

    global_output_paths: list[Path] = []  # All Logger instances everywhere will log to these paths (optional)

    def __init__(
        self,
        log_level: LogLevel = LogLevel.INFO,
        output_paths: list[Path | TextIO] | None = None,
        default_color: PrintColor = PrintColor.COLOR_OFF,
        signature: str | None = None,
        add_caller: bool = True,
        add_timestamps: bool = True,
        ignore_global_paths: bool = False
    ):
        """
        Initializer

        :param log_level: The lowest level at which to log messages
        :param output_paths: Where to send logs (e.g. files, sys.stdout, ...)
        :param default_color: Default logging color for Logger.info (see lumberjack.PrintColor)
        :param signature: If set, this is prepended to all log messages
        :param add_caller: If True, add caller information (i.e FILE:LINE); otherwise, do not
        :param add_timestamps: If True, prepend logs with timestamps
        :param ignore_global_paths: If True, do not obey the global paths logic; otherwise, do
        """

        self.__log_level:         LogLevel   = log_level
        self.add_caller:          bool       = add_caller
        self.add_timestamps:      bool       = add_timestamps
        self.ignore_global_paths: bool       = ignore_global_paths
        self.default_color:       PrintColor = default_color
        self.signature:           str | None = signature

        self.__callbacks: dict[LogLevel, list[CallbackConfig]] = {}

        # Linting anomaly: The linter thinks that sys.stdout is a typing.TextIO but it is actually an io.TextIOWrapper
        self.output_paths: list[Path | TextIO] = output_paths if isinstance(output_paths, list) else [sys.stdout]


    @property
    def log_level(self) -> LogLevel:
        """
        Get the current log level
        """

        return self.__log_level


    @log_level.setter
    def log_level(self, level: LogLevel) -> None:
        """
        Set the new log level (defensively)

        :param level: The new logging level
        """

        if isinstance(level, LogLevel):
            self.__log_level = level
        else:
            self.warning(f'Unrecognized level [{level}]. Defaulting to INFO')
            self.__log_level = LogLevel.INFO


    def banner(self, text: str, color: PrintColor | str = PrintColor.WHITE, symbol: str = '=') -> None:
        """
        Log a message surrounded with a big visible banner

        :param text: Mesage to log
        :param color: Color to print the text
        :param symbol: The symbol to use for the logging banner
        """

        max_header_width: int = 120
        header: str = symbol * int(max_header_width / len(symbol))

        self.__log(LogLevel.INFO, header, color)
        self.__log(LogLevel.INFO, text, color)
        self.__log(LogLevel.INFO, header, color)


    def noise(self, text: str, color: PrintColor | str | None = PrintColor.CYAN) -> None:
        """
        Log message, which will be seen iff the current log level is <= LogLevel.NOISE

        :param text: Mesage to log
        :param color: Color in which to print the text
        :return: None
        """

        self.__log(LogLevel.NOISE, text, color)


    def debug(self, text: str, color: PrintColor | str | None = PrintColor.CYAN) -> None:
        """
        Log message, which will be seen iff the current log level is <= LogLevel.DEBUG

        :param text: Mesage to log
        :param color: Color in which to print the text
        :return: None
        """

        self.__log(LogLevel.DEBUG, text, color)


    def info(self, text: str, color: str | PrintColor | None = None) -> None:
        """
        Log message, which will be seen iff the current log level is <= LogLevel.INFO

        :param text: Mesage to log
        :param color: Color in which to print the text
        :return: None
        """

        self.__log(LogLevel.INFO, text, color)


    def warning(self, text: str, color: PrintColor | str | None = PrintColor.YELLOW) -> None:
        """
        Log message, which will be seen iff the current log level is <= LogLevel.WARNING

        :param text: Mesage to log
        :param color: Color in which to print the text
        :return: None
        """

        self.__log(LogLevel.WARNING, text, color)


    def error(self, text: str, color: PrintColor | str | None = PrintColor.RED) -> None:
        """
        Log message if current log level is LogLevel.ERROR or lower

        :param text: Mesage to log
        :param color: Color in which to print the text
        """

        self.__log(LogLevel.ERROR, text, color)


    def register_callback(
        self,
        log_level: LogLevel,
        callback: Callable[[str], None],
        add_timestamps: bool = True,
        add_caller: bool = True
    ) -> bool:
        """
        Register a callback for a specific log level

        Every time logs are logged at the given level (or below), the callback will be called with the log text

        :param log_level: The maximum log level that the callback should be called for
        :param callback: A function/method that takes a single str and returns nothing
        :param add_timestamps: If True, add timestamps to log messages; otherwise do not
        :param add_caller: If True, add the class/method/line-number that the log came from; otherwise, do not
        :return: True if everything went well; False otherwise
        """

        if log_level not in self.__callbacks:
            self.__callbacks[log_level] = []
        self.__callbacks[log_level].append(
            CallbackConfig(callback, add_timestamps, add_caller)
        )
        return True


    def unregister_callback(self, log_level: LogLevel, callback: Callable[[str], None]) -> bool:
        """
        Unregister a callback for a specific log level

        :param log_level: The log level to unregister a callback from
        :param callback: A function/method that takes a single str and returns nothing
        """

        callbacks: list[CallbackConfig] | None = self.__callbacks.get(log_level)
        if callbacks is None:
            return False
        else:
            self.__callbacks[log_level] = [_config for _config in callbacks if _config.callback != callback]
            return True


    def __log(self, level: LogLevel, text: str, color: PrintColor | str | None = None) -> None:
        """
        Print msg wrapped in the calling method if level is greater than or equal to the current log level

        :param level: A Logger.LOG_LEVEL_XXX value
        :param text: The str to print out
        :param color: Color in which to print the text
        """

        # The inspect package defaults to using the values below when the caller is not in a class and/or method
        default_class_name: str = 'NoneType'
        default_method_name: str = '<module>'

        timestamp:   str | None = None
        class_name:  str | None = None
        method_name: str | None = None
        line_number: int | None = None

        if self.log_level <= level:
            log_label: str = level.name.capitalize()

            if self.add_timestamps:
                timestamp = datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

            if self.add_caller:
                stack:       list[inspect.FrameInfo] = inspect.stack()
                frame:       inspect.FrameInfo       = stack[2]  # 0 --> this method, 2 --> two calls up the stack
                module_name: str                     = frame.filename.split('/')[-1]
                class_name                           = frame[0].f_locals.get('self').__class__.__name__
                method_name                          = frame[3]
                line_number                          = frame[2]

                if class_name == default_class_name:
                    class_name = module_name.replace('.py', '')

            source: str
            preposition: str
            if class_name != default_class_name and method_name != default_method_name:
                source = f'{class_name}.{method_name}:'
                preposition = 'in'
            elif method_name != default_method_name:
                source = f'{method_name}:'
                preposition = 'in'
            else:
                source = ''
                preposition = 'on line'

            caller:    str = f'[{log_label} {preposition} {source}{line_number}]' if self.add_caller else ''
            signature: str = f' [{self.signature}] ' if self.signature is not None else ''
            full_msg:  str = f'[{timestamp}] {caller}{signature}: {text}'
            log_color: PrintColor | str = color or self.default_color or PrintColor.COLOR_OFF

            # Send logs to configured files/streams/etc
            path: Path | TextIO
            for path in self.output_paths:
                if isinstance(path, Path):
                    with open(path, 'a') as _f:
                        _f.write(f'{full_msg}\n')
                elif isinstance(path, io.TextIOWrapper):
                    print_color(full_msg, log_color, path)

            # Send logs to globally-configured files
            if not self.ignore_global_paths:
                for path in Logger.global_output_paths:
                    with open(path, 'a') as _f:
                        _f.write(f'{full_msg}\n')

            # Send logs to any registered subscribers
            for _callback_log_level, _callbacks in self.__callbacks.items():
                if _callback_log_level == level:
                    for _config in _callbacks:
                        _message: str = (
                            f'{signature}'
                            f'[{timestamp}]' if _config.add_timestamps else ''
                            f' {caller}' if _config.add_caller else ''
                            f' {text}'
                        )
                        _config.callback(_message)
