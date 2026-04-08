"""
Module to establish connection and communicate with a serial device. Can be used as standalone tool
"""

from __future__ import annotations

import argparse
import datetime
import logging
import os
import re
import signal
import sys
import threading
import time
import traceback
import types
from abc import ABC, abstractmethod
from re import Pattern
from typing import Iterator, TypeVar

import serial  # type: ignore[import-untyped]
from serial.serialutil import SerialException  # type: ignore[import-untyped]

logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)
logger = logging.getLogger('serial_manager')



def parse_commandline() -> argparse.Namespace:
    """
    Parse commandline arguments
    """

    script = sys.argv[0].split('/')[-1]
    usage = f'{script} <-d /path/to/serial/dev [/path/to/other/serial/dev> [-b baudrate] [-o logfile] [--notimestamps]'
    description = 'A tool to interact with a serial device, automatically adding timestamps and parsing lines nicely'
    epilog = f"""Example:\n{script} -f /dev/cu.SLAB_USBtoUART -o logs.txt"""

    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(script, usage, description, epilog, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        '-d', '--devices',
        help='Path to one or more serial devices',
        nargs='+',
        default=None
    )

    parser.add_argument(
        '-b', '--baudrate',
        help='Serial device(s) baud rate',
        type=int,
        default=115200
    )

    parser.add_argument(
        '-o', '--output',
        help='Where to save log file',
        type=str,
        default=None
    )

    parser.add_argument(
        '--notimestamps',
        help="Don't add timestamps to logs",
        action='store_true',
        default=False
    )

    parser.add_argument(
        '--highlight',
        help='Regex(es) to highlight logs',
        nargs='+',
        default=[]
    )

    parser.add_argument(
        '--script',
        help='Execute commands from a given text file',
        default=None
    )

    parser.add_argument(
        '--script_cooldown',
        help='Time to wait between script commands (used with --script)',
        type=float,
        default=3.0
    )

    args = parser.parse_args()

    if args.devices is None:
        logger.error('Path to at least one serial device is required')
        parser.print_help()
        sys.exit(1)

    highlight_regexes = []
    for regex_str in args.highlight:
        try:
            regex = re.compile(regex_str, flags=re.IGNORECASE)
            highlight_regexes.append(regex)
        except re.error as error:
            logger.error(f'Error: Unable to compile regular expression. "{error}". Regex ignored')

    args.highlight = highlight_regexes

    return args


def get_timestamp() -> str:
    """
    Get a formatted timestamp
    """

    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S.%f")  # %f is microseconds
    return timestamp[:-3]  # truncate microseconds down to milliseconds


class PrintColor:
    """
    High intensity colors (the "regular" ones are '\033[3Xm' (for X in [0..7]) but are too dark)
    Use hexdump -C $(tput setaf <NUMBER>) to see codes
    """

    BLACK  = '\033[90m'
    RED    = '\033[91m'
    ORANGE = '\033[172m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    BLUE   = '\033[94m'
    PURPLE = '\033[95m'
    CYAN   = '\033[96m'
    WHITE  = '\033[97m'

    # Turn off special coloring
    COLOR_OFF = '\033[0m'


class SerialListener(ABC):
    """
    Abstract Base Class providing the structure for any serial listener subclass
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Nickname for the listener
        """


    @abstractmethod
    def handle_event(self, event: str) -> None:
        """
        Callback method called by SerialManager when an event occurs

        :param event: Output from serial device
        """


class SerialClient(SerialListener):
    """
    Class that can both send commands to and listen to the output of a serial device via the SerialManager
    """

    def __init__(
        self,
        name: str,
        managers: list['SerialManager'] | None = None,
        output_path: str | None = None,
        log_to_stdout: bool = False,
        silent: bool = False
    ) -> None:
        """
        Initializer

        :param name: Nickname to give the client
        :param managers: An instance of a SerialManager
        :param output_path: Path to save logs to (or None to not save logs)
        :param log_to_stdout: If True, logging is also printed to stdout; otherwise not
        :param silent: If True, do not log anything when sending commands
        """

        self.__talking_stick = threading.Lock()
        self.command_output = ''

        self.__name = name
        self.__managers = managers or []
        self.output_path = output_path
        self.log_to_stdout = log_to_stdout
        self.silent = silent

        if self.output_path is not None:
            logger.info(f'Saving logs to {output_path}')
            with open(self.output_path, 'a', encoding='utf-8'):
                pass  # make sure file gets created

        for manager in self.__managers:
            if manager is None:
                continue
            manager.register_listener(self)


    @property
    def name(self) -> str:
        return self.__name


    def __wait_for_processing_to_complete(self, command: str, manager_index: int) -> None:
        """
        Wait for serial manager output processing to complete and then return

        :param command: The command to wait for
        :param manager_index: Which manager to listen for (or None to wait for all)
        """

        manager = self.__managers[manager_index]

        # Wait for command to start processing
        while command in manager.command_queue:
            time.sleep(0.05)

        # Wait for the serial device to start sending output
        while not manager.is_processing_output:
            time.sleep(0.05)

        # Serial buffer size is 1020 bytes, which means that manager.is_processing_output can start+stop+start+stop
        # repeatedly. To combat this, we assume that output processing is complete when the link is quiet for a
        # specific amount of time
        assumed_done_time = 1.0
        idle_time = 0
        output_processing_timestamp = time.time()
        while idle_time < assumed_done_time:
            if manager.is_processing_output:
                idle_time = 0
                output_processing_timestamp = time.time()
            else:
                idle_time = time.time() - output_processing_timestamp
            time.sleep(0.05)


    def handle_event(self, event: str) -> None:
        """
        Callback method called by SerialManager when an event occurs

        :param event: Output from serial device
        """

        logger.debug(f'"{self.name}" received event: "{event.strip()}"')

        with self.__talking_stick:
            self.command_output += event
            if self.log_to_stdout:
                print(event.strip())  # use print instead of logger to avoid double-timestamping

            if self.output_path is not None:
                with open(self.output_path, 'a', encoding='utf-8') as f:
                    f.write(event)


    def send_command(self, command: str, manager_index: int | None = None, expect_output: bool = True) -> str | None:
        """
        Send a command to the serial device

        :param command: Command to send
        :param manager_index: If client is registered with multiple manager, specify which one to send command to
        :param expect_output: If True, wait for output from serial device; otherwise do not
        :return: The output of the command (plus w/e serial may have output) if output is expected; otherwise None
        """

        if not command.isprintable():
            a = [ord(c) for c in command]
            logger.warning(f'Rejecting unexpected command with unprintable characters. ASCII values: {a}')
            return None

        if not self.silent:
            command_str = '<ENTER KEY>' if command == '\n' else f'"{command}"'
            logger.info(f'[{self.name}] Sending command to serial device: {command_str}')
            logger.debug(f'Traceback:\n{"".join(traceback.format_stack())}')

        with self.__talking_stick:
            self.command_output = ''

        if manager_index is not None:
            self.__managers[manager_index].queue_command(command)
            if expect_output:
                self.__wait_for_processing_to_complete(command, manager_index)
        else:
            for i, _manager in enumerate(self.__managers):
                _manager.queue_command(command)
                if expect_output:
                    self.__wait_for_processing_to_complete(command, i)

        if not expect_output:
            return None

        with self.__talking_stick:
            output = self.command_output
        return output


SerialListenerTypeT = TypeVar('SerialListenerTypeT', bound=SerialListener)


class SerialManager(threading.Thread):
    """
    Publisher Thread

    Responsible for sending commands to and receiving output from the serial device.
    Communicating with the serial device is done via subscribers
    """

    def __init__(
        self,
        name: str,
        device_path: str,
        baud_rate: int = 115200,
        add_timestamps: bool = True,
        highlight_regexes: list[Pattern[str]] | None = None,
        start: bool = False
    ) -> None:
        """
        Initializer

        :param name: Nickname for the manager
        :param device_path: Path to the serial device (e.g. '/dev/cu.SLAB_USBtoUART123')
        :param baud_rate: Number of signal changes occurring per second (commonly 115200)
        :param add_timestamps: If True, timestamps are automatically added to serial output
        :param highlight_regexes: List of regular expression strings to use for highlighting bits of logs
        :param start: If True, thread will start immediately. Otherwise, user will have to call start() method
        """

        super().__init__()

        self.daemon = True
        self.__talking_stick = threading.Lock()
        self.__stop_event = threading.Event()
        self.__processing_input = False  # input to this system from the serial device

        self.device:            serial.Serial | None = None
        self.listeners:         list[SerialListener] = []
        self.name:              str = name
        self.device_path:       str = device_path
        self.baud_rate:         int = baud_rate
        self.add_timestamps:    bool = add_timestamps
        self.highlight_regexes: list[Pattern[str]] = highlight_regexes or []

        # Commands to be sent to the serial device
        self.__command_queue: list[str] = []

        if start:
            self.start()


    @property
    def command_queue(self) -> list[str]:
        """
        Get a copy (for protection) of the command queue
        """

        with self.__talking_stick:
            return self.__command_queue[:]


    @property
    def is_processing_output(self) -> bool:
        """
        Check whether the manager is currently processing output from the serial device

        :return: True if manager is currently processing output from serial device; False otherwise
        """

        with self.__talking_stick:
            return self.__processing_input


    def notify_listeners(self, event: str) -> None:
        """
        Notify all registered listeners of an event

        :param event: Output from serial device
        """

        for regex in self.highlight_regexes:
            for substring in regex.findall(event):
                # Wrap substring in colorizing control codes
                event = event.replace(substring, f'{PrintColor.CYAN}{substring}{PrintColor.COLOR_OFF}')

        logger.debug(f'event: "{event.strip()}"')
        with self.__talking_stick:
            self.listeners = [_listener for _listener in self.listeners if _listener is not None]
            for listener in self.listeners:
                logger.debug(f'Send event to listener: {listener.name}')
                listener.handle_event(event)


    def queue_command(self, command: str, cooldown: float = 0.0) -> None:
        """
        Queue up a new command to send to the serial device

        :param command: Command to send to the serial device
        :param cooldown: Optional amount of time in seconds to wait after queuing the command
        """

        with self.__talking_stick:
            self.__command_queue.append(command)
        time.sleep(cooldown)


    def register_listener(self, listener: SerialListener) -> None:
        """
        Add listener

        :param listener: Any subclass of SerialListener
        """

        with self.__talking_stick:
            self.listeners.append(listener)
            count = len(self.listeners)
            logger.debug(f'[{self.name}] Registered listener: "{listener.name}" (num listeners: {count})')


    def unregister_listener(self, listener: SerialListener) -> None:
        """
        Remove listener

        :param listener: Any subclass of SerialListener
        """

        with self.__talking_stick:
            if listener in self.listeners:
                self.listeners.remove(listener)
                count = len(self.listeners)
                logger.debug(f'[{self.name}] Unregistered listener: "{listener.name}" (num listeners: {count})')


    def stop(self) -> None:
        """
        Signal the thread to stop running
        """

        self.__stop_event.set()


    def __process_serial_data(self, raw: bytes) -> Iterator[str]:
        """
        Generator Method

        Split raw bytes from the serial device into lines, prepending timestamps to each

        :param raw: Raw bytes read from the serial device
        """

        text = raw.decode(encoding='utf-8', errors='ignore')
        lines = text.split('\n')

        for line in lines[:-1]:  # last line may be incomplete
            timestamp = f'[{get_timestamp()}] ' if self.add_timestamps else ''
            yield f'{timestamp}{line}\n'

        # Keep the last (possibly incomplete) fragment for the caller to handle
        if lines[-1]:
            timestamp = f'[{get_timestamp()}] ' if self.add_timestamps else ''
            yield f'{timestamp}{lines[-1]}\n'


    def run(self) -> None:
        """
        Called when the thread starts
        """

        # Establish connection to serial device
        with self.__talking_stick:
            try:
                self.device = serial.Serial(
                    port=self.device_path,
                    baudrate=self.baud_rate,
                    timeout=0.05  # Short timeout so blocking read() yields control quickly for command processing
                )
                logger.debug(f'[{self.name}] Connection established to {self.device_path}')

            except SerialException as error:
                logger.error(f'Error: Could not connect to serial device. Message: "{error}"')
                return

        # Main thread loop — uses blocking read() with a short timeout instead of polling + sleep.
        # read(1) blocks for up to 50ms waiting for data. When data arrives, we greedily read
        # everything available. Commands are checked every iteration (~50ms) instead of every ~1s.
        while not self.__stop_event.is_set():
            with self.__talking_stick:
                command = self.__command_queue.pop(0) if len(self.__command_queue) > 0 else None

            if command is not None:
                logger.debug(f'Processing command: {command}')
                self.device.write(f'{command}\n'.encode())

            # Block for up to timeout (50ms) waiting for at least 1 byte
            max_attempts = 10
            data = b''
            for i in range(max_attempts):
                try:
                    data = self.device.read(1)
                    break
                except SerialException as error:
                    print(f'[{self.name}] [{i} of {max_attempts}] Failed to read from serial. Error: "{error}"')
                    continue

            if data:
                # Greedily read everything else that's available right now
                remaining = self.device.in_waiting
                if remaining > 0:
                    for i in range(max_attempts):
                        try:
                            data += self.device.read(remaining)
                            break
                        except SerialException as error:
                            print(
                                f'[{self.name}] [{i} of {max_attempts}] '
                                f'Failed to read remaining from serial. Error: "{error}"'
                            )
                            continue

                with self.__talking_stick:
                    logger.debug(f'Processing input... ({len(data)} bytes)')
                    self.__processing_input = True
                for line in self.__process_serial_data(data):
                    self.notify_listeners(line)
                with self.__talking_stick:
                    logger.debug('Done processing input')
                    self.__processing_input = False

        logger.debug(f'[{self.name}] Thread loop stopped')
        self.device.close()


def main() -> None:
    """Main entry point"""

    def handle_sigint(_signum: int, _frame: types.FrameType | None) -> None:
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_sigint)  # Pressing CTRL+c sends SIGINT and exits
    args = parse_commandline()

    managers = [
        SerialManager(
            name=device,
            device_path=device,
            baud_rate=args.baudrate,
            add_timestamps=not args.notimestamps,
            highlight_regexes=args.highlight,
            start=True
        )
        for device in args.devices
    ]

    name = os.environ.get('USER') or 'user'
    client = SerialClient(name, managers, output_path=args.output, log_to_stdout=True)

    # Execute script if one was specified
    if args.script is not None:
        with open(args.script, encoding='utf-8') as f:
            commands = f.readlines()
        logger.info(f'Executing script commands from "{args.script}":')
        for command in commands:
            if len(command.strip()) > 0:
                client.send_command(command.strip())
                time.sleep(args.script_cooldown)

    # Allow user to send commands to serial device(s)
    print('Enter commands at "> " prompt or type "quit" to exit')
    while True:
        command = input('> ')
        if command.lower() in ['quit']:
            sys.exit(0)
        elif command.strip() == '':
            continue
        else:
            client.send_command(command.strip())


if __name__ == '__main__':
    main()
