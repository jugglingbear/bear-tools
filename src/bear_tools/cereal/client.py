import io
import os
import select
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Sequence, TextIO

from bear_tools import cereal, lumberjack
from bear_tools.cereal.mods.base import LoggingModBase
from bear_tools.cereal.tokenizer import Tokenizer
from bear_tools.network_utils import wait_for_server
from bear_tools.thread_utils import wait_for_thread_to_start

normal_logger = lumberjack.Logger()

DEBUG_SIGNATURE = '[cereal]'


class CerealClient(threading.Thread):
    """
    Cereal Client

    - Receives serial logging from a CerealServer
    - Can send messages (commands) indirectly to the serial device through the server
        - Can optionally obtain output of commands
    """

    BUFFER_SIZE: int = 1024

    def __init__(
        self,
        name: str,
        address: str,
        port: int,
        output: Sequence[Path | TextIO | io.TextIOBase | list[str]],
        mods: list[LoggingModBase] | None = None,
        start: bool = True,
        default_annotation_emoji: str = '📡'
    ) -> None:
        """
        Initializer

        :param name: Nickname for the client
        :param address: The server address
        :param port: The server port
        :param output: Send logs to this list of file paths and/or standard streams (e.g. sys.stdout, sys.stderr)
        :param mods: A list of logging mods to register and run
        :param start: If True, start the thread immediately when read; otherwise, do not
        :param default_annotation_emoji: Emoji used to wrap annotation banners when no per-call emoji is given
        """

        self.logger = lumberjack.Logger(lumberjack.LogLevel.INFO, add_caller=False, ignore_global_paths=True)

        super().__init__()
        self.daemon = True
        errors_found: bool = False

        self.name:    str                                                 = name
        self.address: str                                                 = address
        self.port:    int                                                 = port
        self.output:  Sequence[Path | TextIO | io.TextIOBase | list[str]] = output
        self.default_annotation_emoji: str                                = default_annotation_emoji

        self._pipes_closed: bool = False

        # Pipe used for processing special commands (e.g. '__quit'). These are not sent to the server
        self.command_pipe_read:  int = -1
        self.command_pipe_write: int = -1
        self.message_pipe_read:  int = -1
        self.message_pipe_write: int = -1

        try:
            self.command_pipe_read, self.command_pipe_write = os.pipe()
        except OSError as error:
            self.logger.error(f'Failed to create command pipes. Error: "{error}"')
            errors_found = True

        # Pipe used for sending messages to the server, which relays them to the serial device
        try:
            self.message_pipe_read, self.message_pipe_write = os.pipe()
        except OSError as error:
            self.logger.error(f'Failed to create message pipes. Error: "{error}"')
            self._close_pipes()
            errors_found = True

        # Temporary buffer used to hold messages received from the server (serial output)
        # This is for when the user calls send(..., expect_output=True)
        self.__messages_lock = threading.Lock()
        self.__messages: list[str] = []
        self._capturing: bool = False  # Only collect messages when a send(expect_output=True) is in progress

        # Special logging mods that perform specific actions based on the contents of logging
        self.logging_mods: list[LoggingModBase] = mods or []

        if start:
            if errors_found:
                self.logger.warning('Not starting cereal client. Errors occurred during initialization')
            else:
                self.start()
                if not wait_for_thread_to_start(self):
                    self.logger.error('Thread failed to start')


    def _close_pipes(self) -> None:
        """
        Close all pipe file descriptors (safe to call multiple times)
        """

        if self._pipes_closed:
            return
        self._pipes_closed = True

        for fd in [self.command_pipe_read, self.command_pipe_write,
                   self.message_pipe_read, self.message_pipe_write]:
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass


    def __send_message(self, sock: socket.socket, data: bytes) -> None:
        """
        Send a message to the server

        :param sock: The socket to use for sending
        :param data: The data to send
        """

        text = data.decode('utf-8')
        self.logger.info(f'Sending message to server: "{text}"')
        sock.sendall(data + cereal.END_OF_MESSAGE)


    def __setup_logging(self, output: Sequence[Path | TextIO | io.TextIOBase | list[str]]) -> None:
        """
        Setup the logging to send logs to the specified files and/or standard streams
        """

        if len(output) > 0:
            for _path in output:
                if isinstance(_path, Path):
                    _path.parent.mkdir(parents=True, exist_ok=True)
            self.logger.outputs = list(output)

            _description: list[str] = [str(_item) for _item in output if isinstance(_item, Path)]
            _description += ['stdout' for _item in output if _item == sys.stdout]
            _description += ['stderr' for _item in output if _item == sys.stderr]
            self.logger.info(f'[{self.name}] Sending logs to: {", ".join(_description)}')
        else:
            self.logger.warning('Uh... logs are set to go nowhere. Did you forget to set some flags?')
            self.logger.outputs = list(output)


    def __wait_for_logging_to_start(
        self,
        timeout_sec: float,
        command_echo: str = '',
        polling_period_sec: float = 0.050
    ) -> bool:
        """
        Wait for logging from the server to start (as a result of sending a command to the server)

        If command_echo is provided, waits until a message containing the echoed command is seen, then
        discards all messages received before (and including) the echo line so that only the command's
        actual output is returned. Falls back to detecting any output if no echo is seen within timeout.

        :param timeout_sec: How long to wait (seconds) for the logging to start
        :param command_echo: The command string to look for as an echo marker (empty string disables echo matching)
        :param polling_period_sec: How long to wait (seconds) between each status check
        :return: True if the server sent something back within timeout_sec
        """

        start_time: float = time.perf_counter()
        while time.perf_counter() - start_time <= timeout_sec:
            with self.__messages_lock:
                if command_echo:
                    # Look for the echoed command in the accumulated messages
                    for i, msg in enumerate(self.__messages):
                        if command_echo in msg:
                            # Discard everything up to and including the echo line
                            self.__messages = self.__messages[i + 1:]
                            self.logger.debug(f'{DEBUG_SIGNATURE} Echo detected, capturing output')
                            return True
                elif len(self.__messages) > 0:
                    self.logger.debug(f'{DEBUG_SIGNATURE} Logging from server started')
                    return True
            time.sleep(polling_period_sec)

        # Fallback: if echo matching was requested but timed out, check if we have any data at all
        if command_echo:
            with self.__messages_lock:
                if len(self.__messages) > 0:
                    self.logger.debug(
                        f'{DEBUG_SIGNATURE} Echo not found for "{command_echo}", '
                        f'falling back to {len(self.__messages)} collected messages'
                    )
                    return True

        self.logger.error(f'No output from server for {timeout_sec:.2f} seconds')
        return False


    def __wait_for_logging_to_stop(
        self,
        timeout_sec: float,
        idle_timeout_sec: float = 1.0,
        polling_period: float = 0.100
    ) -> bool:
        """
        Wait for logging from the server to stop coming in

        :param timeout_sec: How long to wait (seconds) for the logging to stop
        :param idle_timeout_sec: Time (seconds) without a new message from server before we assume logging is done
        :param polling_period: How long to wait in between each check
        :return: True if the server stopped sending logs
        """

        self.logger.debug(f'{DEBUG_SIGNATURE} timeout_sec: {timeout_sec}, idle_timeout_sec: {idle_timeout_sec}')

        idle_time: float = 0.0
        previous_message_count: int = -1
        message_processed_timestamp = time.perf_counter()  # Assumption: We just processed a new message from the server

        start_time: float = time.perf_counter()
        while True:
            time_elapsed: float = time.perf_counter() - start_time
            self.logger.debug(f'{DEBUG_SIGNATURE} idle_time: {idle_time:.2f} sec, time_elapsed: {time_elapsed:.2f} sec')

            if time_elapsed > timeout_sec:
                break
            elif idle_time > idle_timeout_sec:
                self.logger.debug(f'{DEBUG_SIGNATURE} No new logging from server for {idle_time} sec')
                return True
            else:
                with self.__messages_lock:
                    messages_count = len(self.__messages)
                if messages_count != previous_message_count:
                    idle_time = 0.0
                    previous_message_count = messages_count
                    message_processed_timestamp = time.perf_counter()
                else:
                    idle_time = time.perf_counter() - message_processed_timestamp
            time.sleep(polling_period)

        self.logger.warning(f'{DEBUG_SIGNATURE} Logging did not stop within {timeout_sec} sec. Data may be incomplete')
        return False


    def run(self) -> None:
        """
        Main thread loop
        """

        message_buffer: bytearray = bytearray()       # Buffer for messages sent to the server
        tokenizer = Tokenizer(cereal.END_OF_MESSAGE)  # Used to parse (blob) messages from server into list[str]

        self.__setup_logging(self.output)
        if not wait_for_server(self.address, self.port):
            normal_logger.error(f'Server not found or is not connectable: {self.address}:{self.port}')
            return

        # Connect to the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((self.address, self.port))
            except ConnectionRefusedError:
                self.logger.error('Unable to connect to server: Connection refused')
                return

            file_descriptors: list[int | socket.socket] = [self.command_pipe_read, self.message_pipe_read, sock]
            try:
                while True:
                    # Wait for readable data to arrive on any file descriptors
                    readable_file_descriptors, _, _ = select.select(file_descriptors, [], file_descriptors)

                    # (Client --> Client) Handle special client commands
                    if self.command_pipe_read in readable_file_descriptors:
                        command_code: bytes = os.read(self.command_pipe_read, self.BUFFER_SIZE)
                        if command_code == cereal.CLIENT_COMMAND_CODE_QUIT:
                            break
                        self.logger.error(f'Unexpected command code: {command_code.hex(":")}')
                        continue

                    # (Client --> Server)
                    if self.message_pipe_read in readable_file_descriptors:
                        partial_message: bytes = os.read(self.message_pipe_read, self.BUFFER_SIZE)
                        message_buffer += partial_message

                        while True:
                            index = message_buffer.find(cereal.END_OF_MESSAGE)
                            if index < 0:
                                break
                            message: bytes = message_buffer[:index]
                            self.__send_message(sock, message)
                            message_buffer = message_buffer[index + len(cereal.END_OF_MESSAGE):]

                    # (Server --> Client)
                    elif sock in readable_file_descriptors:
                        data: bytes = sock.recv(self.BUFFER_SIZE)
                        if len(data) == 0:
                            break  # connection terminated

                        # Save the output in case user wanted it (i.e. send(..., expect_output=True))
                        tokenizer.add(data)
                        for _data in tokenizer.tokens:
                            _text: str = _data.decode('utf-8').strip()
                            self.logger.info(_text)  # Send logging to files/streams

                            for logging_mod in self.logging_mods:
                                logging_mod.handle_event(_text)

                            if self._capturing:
                                with self.__messages_lock:
                                    for _line in _text.split('\n'):
                                        self.__messages.append(_line.strip())
                        tokenizer.tokens.clear()
            finally:
                self._close_pipes()

        self.logger.info('Disconnected from server')


    def send(self, text: str, expect_output: bool = False, timeout_sec: float = 10.0) -> list[str]:
        """
        Send a message (command) to the server. Automatically annotates the log stream so serial commands
        are visually distinct.

        :param text: Message (command) to send
        :param expect_output: If True, return device output up to {timeout_sec} after sending the message
        :param timeout_sec: How long to wait for expected output to start+stop before returning whatever we have
        :return: If {expect_output}, a list[str] containing output observed a result of sending {text}; otherwise, []
        """

        self.annotate(f'SENDING: {text}', emoji='📡')
        return self._send_raw(text, expect_output=expect_output, timeout_sec=timeout_sec)


    def _send_raw(self, text: str, expect_output: bool = False, timeout_sec: float = 10.0) -> list[str]:
        """
        Low-level send: write a message to the server without triggering an annotation.
        Used internally by :meth:`send` and :meth:`annotate`.

        :param text: Message (command) to send
        :param expect_output: If True, return device output up to {timeout_sec} after sending the message
        :param timeout_sec: How long to wait for expected output to start+stop before returning whatever we have
        :return: If {expect_output}, a list[str] containing output observed a result of sending {text}; otherwise, []
        """

        # Clear temporary buffer that holds output and enable capture
        with self.__messages_lock:
            self.__messages.clear()
        self._capturing = expect_output

        # Send (message + terminator) to the main thread loop so it can be sent to the server
        self.logger.debug(f'{DEBUG_SIGNATURE} sending text to server: "{text}" (timeout_sec: {timeout_sec})')
        data: bytes = text.encode('utf-8')
        message: bytes = data + cereal.END_OF_MESSAGE
        try:
            os.write(self.message_pipe_write, message)
        except OSError as error:
            self._capturing = False
            self.logger.error(
                f'Failed to os.write message to write pipe: {message.hex(":")}, '
                f'read pipe fd: {self.message_pipe_read}, '
                f'write pipe fd: {self.message_pipe_write}, '
                f'Error: "{error}"'
            )

        if not expect_output:
            return []

        # Wait for output --> The server should start+finish sending logs in response to the msg/command we sent
        # Use the sent command as an echo marker to filter out ambient serial noise
        if not self.__wait_for_logging_to_start(timeout_sec, command_echo=text):
            self._capturing = False
            return []
        self.__wait_for_logging_to_stop(timeout_sec)
        self._capturing = False

        with self.__messages_lock:
            messages = self.__messages[:]

        self.logger.debug(f'{DEBUG_SIGNATURE} Output from the device:')
        for _line in messages:
            self.logger.debug(f'{DEBUG_SIGNATURE}     {_line}')

        return messages


    def annotate(self, text: str, emoji: str | None = None) -> None:
        """
        Inject a synthetic annotation into the log stream via the server. The annotation is broadcast to all
        connected clients but is never sent to the serial device.

        :param text: The annotation text to inject
        :param emoji: The emoji used to wrap the annotation banner (default: instance default_annotation_emoji)
        """

        emoji = emoji or self.default_annotation_emoji

        self._send_raw(f'{cereal.SERVER_COMMAND_ANNOTATE}{emoji}:{text}')


    def stop(self) -> None:
        """
        Signal the thread to stop
        """

        if self.is_alive():
            try:
                os.write(self.command_pipe_write, cereal.CLIENT_COMMAND_CODE_QUIT)
            except OSError:
                pass
            self.join()


    def __str__(self) -> str:
        return f'<Name: "{self.name}", address: "{self.address}", port: {self.port}>'
