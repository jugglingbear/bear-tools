from __future__ import annotations

import collections
import io
import os
import select
import socket
import socketserver
import subprocess
import sys
from pathlib import Path
from typing import Any, TextIO, cast

from bear_tools import cereal, lumberjack
from bear_tools.cereal.serial_manager import SerialListener, SerialManager
from bear_tools.cereal.tokenizer import Tokenizer
from bear_tools.network_utils import is_port_in_use, wait_for_server

color = lumberjack.PrintColor.GREEN  # highlight color
ClientAddress = collections.namedtuple('ClientAddress', 'ip_address, port_number')
cereal_server: CerealServer | None


class Listener(SerialListener):
    """
    Base class used to send serial logs to stdout and/or files
    """

    def __init__(self, logger: lumberjack.Logger):
        """
        Initializer

        :param logger: The logger configured for the parent class
        """

        self.logger = logger


    @property
    def name(self) -> str:
        """
        (Override: SerialListener)
        Nickname for the listener
        """

        return 'Cereal-Client'


    def handle_event(self, event: str) -> None:
        """
        (Override: SerialListener)
        Callback method called by SerialManager when an event occurs (i.e. new serial logging arrives)

        :param event: Logging from serial device
        """

        self.logger.info(event.strip())


class CerealServer(socketserver.ThreadingTCPServer):
    """
    A server that communicates with a serial device and allows multiple clients to connect to do serial I/O
    """

    # Overriden values from base class
    allow_reuse_address = True  # Allow server to bind to in-use address:port to prevent quick-restart errors
    daemon_threads = True       # All clients should be daemon threads that end when main process ends

    BUFFER_SIZE: int = 1024

    def __init__(
        self,
        name: str,
        address: str,
        port: int,
        device_path: Path,
        output: list[Path | TextIO | io.TextIOBase | list[str]],
        buffer_size: int = BUFFER_SIZE
    ):
        """
        Initializer

        :param name: Nickname for the server (e.g. 'RTOS', 'Linux')
        :param address: The ipaddress or host name on which the server should listen
        :param port: The port number that the server communicates through
        :param device_path: The path to a serial device
        :param output: Path to where to save logs
        :param buffer_size: Maximum message size to receive
        """

        self.logger = lumberjack.Logger(lumberjack.LogLevel.INFO, add_caller=False, ignore_global_paths=True)

        if not device_path.exists():
            self.logger.error(f'Device path not found: "{device_path}". Server cannot start. Expect errors')
            raise FileNotFoundError(f'Serial device not found: "{device_path}"')

        super().__init__(server_address=(address, port), RequestHandlerClass=ClientHandler)

        self.name:        str                                             = name
        self.address:     str                                             = address
        self.port:        int                                             = port
        self.device_path: Path                                            = device_path
        self.output:      list[Path | TextIO | io.TextIOBase | list[str]] = output  # Log to files, buffer or sys.stdout
        self.buffer_size: int                                             = buffer_size

        self.serial_manager = SerialManager(name, str(device_path), add_timestamps=False, start=True)
        self.serial_manager.register_listener(Listener(self.logger))  # Server is serial client too so it can save logs

        self.__setup_logging(self.output)
        self.logger.info(f'"{self.name}" server online and ready to accept new clients', color=color)


    def __setup_logging(self, output: list[Path | TextIO | io.TextIOBase | list[str]]) -> None:
        """
        Setup the logging to send logs to the specified files and/or standard streams

        :param output: Where should all the logging be sent?
        """

        if len(output) > 0:
            for _path in output:
                if isinstance(_path, Path):
                    _path.parent.mkdir(parents=True, exist_ok=True)
            self.logger.outputs = output

            _description: list[str] = [str(_item) for _item in output if isinstance(_item, Path)]
            _description += ['stdout' for _item in output if _item == sys.stdout]
            _description += ['stderr' for _item in output if _item == sys.stderr]
            self.logger.info(f'Sending logs to: {", ".join(_description)}', color=color)
        else:
            self.logger.warning('Uh... logs are set to go nowhere. Did you forget to set some flags?')


class ClientHandler(socketserver.BaseRequestHandler, Listener):
    """
    (Callback for Server (socketserver.ThreadingTCPServer) class)
    Handles client connections

    Class that handles messaging to/from clients that connect to the Server

    Example:
        Client sending commands to server to relay to serial device
        Server sending serial logging to connected clients
    """

    def __init__(self, request: Any, client_address: Any, server: Any) -> None:
        """
        Initializer
        """

        super().__init__(request, client_address, server)

        # Pipe used to pass along serial logging to a client. Logging is written to the "write" end of the pipe
        # and subsequently read from the "read" end and sent across the network to clients
        #
        #                          ▓▀▀▀▀▀▀P▀I▀P▀E▀▀▀▀▀▀▀▓
        # Serial device logs --->  ▓ Write         Read ▓ ---> TCP client
        #                          ▓▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▓
        self.pipe_serial_read_fd:  int = -1  # Initialized in handle
        self.pipe_serial_write_fd: int = -1  # Initialized in handle


    def handle_event(self, event: str) -> None:
        """
        (Override: SerialListener)
        Callback method called by SerialManager when an event occurs (i.e. new serial logging arrives)

        Note: This is called once for each of N connected clients so any debug logging added will be duplicated N times!

        :param event: Logging from serial device
        """

        os.write(self.pipe_serial_write_fd, event.encode('utf-8'))


    def handle(self) -> None:
        """
        (Override: socketserver.BaseRequestHandler)
        Handle a new client request (connection)
        """

        # Values defined by base class: socketserver.BaseRequestHandler
        self.client_address: ClientAddress  # e.g. ('127.0.0.1', 53181)
        self.request:        socket.socket
        self.server = cast(CerealServer, self.server)

        self.server.serial_manager.register_listener(self)
        client_msg_tokenizer = Tokenizer(sentinel=cereal.END_OF_MESSAGE)
        serial_line_tokenizer = Tokenizer(sentinel=b'\n')  # Separate serial data into lines of logging

        self.pipe_serial_read_fd, self.pipe_serial_write_fd = os.pipe()
        file_descriptors: list[int | socket.socket] = [self.pipe_serial_read_fd, self.request]

        # Main thread loop
        self.server.logger.info(f'Client connected: {self.client_address}', color=color)
        try:
            while True:
                try:
                    data: bytes
                    # Wait for data to be available from the pipe or the socket
                    readable_file_descriptors, _, _ = select.select(file_descriptors, [], file_descriptors)

                    # (Serial Device --> Server) Send data to client one line at a time
                    if self.pipe_serial_read_fd in readable_file_descriptors:
                        data = os.read(self.pipe_serial_read_fd, self.server.buffer_size)
                        serial_line_tokenizer.add(data)
                        for _line in serial_line_tokenizer.tokens:
                            self.request.sendall(_line + cereal.END_OF_MESSAGE)
                        serial_line_tokenizer.tokens.clear()

                    # (Client --> Server) Relay the message/command to the serial device
                    if self.request in readable_file_descriptors:
                        data = self.request.recv(self.server.buffer_size)
                        if len(data) == 0:
                            self.server.logger.info(f'Client disconnected: {self.client_address}', color=color)
                            break

                        client_msg_tokenizer.add(partial_message=data)
                        for _data in client_msg_tokenizer.tokens:
                            _text: str = _data.decode('utf-8')

                            # Handle special server commands
                            if _text == cereal.SERVER_COMMAND_CODE_SHUTDOWN:
                                self.server.logger.info('Received command to shutdown server. Shutting down...')
                                self.server.shutdown()
                            elif _text.startswith(cereal.SERVER_COMMAND_ANNOTATE):
                                payload = _text[len(cereal.SERVER_COMMAND_ANNOTATE):]
                                emoji, _, annotation = payload.partition(':')
                                banner = f'{emoji * 15} {annotation} {emoji * 15}'
                                self.server.serial_manager.notify_listeners(f'{banner}\n')
                            elif _text == cereal.SERVER_COMMAND_GET_CONFIG:
                                _paths = [str(_path) for _path in self.server.output if isinstance(_path, Path)]
                                _stdout = ['stdout' for _path in self.server.output if _path == sys.stdout]
                                _stderr = ['stderr' for _path in self.server.output if _path == sys.stderr]
                                _config: bytes = str({
                                    'name': self.server.name,
                                    'device_path': str(self.server.device_path),
                                    'output': sorted(list(set(_paths + _stdout + _stderr)))
                                }).encode('utf-8')
                                self.request.sendall(_config + cereal.END_OF_MESSAGE)

                            # Send text/command to the serial device
                            else:
                                self.server.logger.info(f'Send command from client to serial device: "{_text}"', color)
                                self.server.serial_manager.queue_command(_text)
                        client_msg_tokenizer.tokens.clear()

                except BrokenPipeError:
                    self.server.logger.warning(f'Client {self.client_address} disconnected. Reason: BrokenPipeError')
                    break
                except ConnectionResetError:
                    self.server.logger.warning(
                        f'Client {self.client_address} disconnected. Reason: ConnectionResetError'
                    )
                    break
                except OSError:
                    # This happens when a client is still connected and the server shuts down.
                    # The socket (self.request) gets closed and calling select.select(...) on it results in this error
                    self.server.logger.warning('Server closed our socket. I guess we are done! 👋')
                    break
        finally:
            self.request.close()
            self.server.serial_manager.unregister_listener(self)
            try:
                os.close(self.pipe_serial_read_fd)
            except OSError:
                pass
            try:
                os.close(self.pipe_serial_write_fd)
            except OSError:
                pass


def start_cereal_server(
    name: str,
    device_path: Path,
    address: str,
    port: int,
    output: list[Path],
    log_to_stdout: bool = False
) -> bool:
    """
    Utility to start CerealServer on separate process in the background so any app/thread/script can use it
    via a CerealClient

    :param name: A nickname for the server
    :param device_path: The path to a serial device for the server to interface with
    :param address: The address that the server should run on
    :param port: The port the server should run on
    :param output: Save logs to these paths
    :param log_to_stdout: If True, all server and serial logs will be sent to stdout
    :return: True if the server started successfully; False otherwise
    """

    logger = lumberjack.Logger()
    process: subprocess.Popen[bytes] | None = None

    if not is_port_in_use(address, port):
        # Start server in new process so it outlives this script
        _args: list[str | Path] = ['cereal_server', name, device_path, address, str(port)]
        if len(output) > 0:
            _args.extend(['--output'] + [str(_path) for _path in output])
        if log_to_stdout:
            _args.append('--log_to_stdout')
        process = subprocess.Popen(_args, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    # Is everyting working?
    if wait_for_server(address, port):
        pid: str = f'(pid: {process.pid})' if isinstance(process, subprocess.Popen) else ''
        logger.info(f'{name} serial server running on {address}:{port} {pid}')
        return True
    logger.error(f'{name} server failed to start on {address}:{port}')
    return False
