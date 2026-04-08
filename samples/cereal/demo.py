#!/usr/bin/env python3
"""
bear_tools.cereal integration demo

Starts a CerealServer backed by a pseudo-terminal (no real serial device needed),
connects a CerealClient, sends a few commands, and shows annotations in the log stream.

Usage:
    poetry run python3 samples/cereal/demo.py
"""

from __future__ import annotations

import os
import pty
import signal
import sys
import threading
import time
from pathlib import Path

from bear_tools.cereal import SERVER_ADDRESS
from bear_tools.cereal.client import CerealClient
from bear_tools.cereal.server import CerealServer
from bear_tools.network_utils import is_port_in_use

DEMO_PORT = 19999  # Use a throwaway port so we don't collide with real servers


def _kill_port(port: int) -> None:
    """Kill any process holding the demo port (leftover from a previous crashed run)."""
    if not is_port_in_use(SERVER_ADDRESS, port):
        return
    import subprocess
    result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
    for pid in result.stdout.strip().splitlines():
        os.kill(int(pid), signal.SIGKILL)
    # Wait for OS to fully release the port
    for _ in range(20):
        time.sleep(0.25)
        if not is_port_in_use(SERVER_ADDRESS, port):
            break
    print(f'⚠️  Killed leftover process on port {port}')


# ---------------------------------------------------------------------------
# Fake serial device — a pty that echoes back whatever is written to it
# ---------------------------------------------------------------------------
class FakeSerialDevice:
    """Opens a pty pair. The 'slave' path acts as the serial device for CerealServer.
    A background thread reads the master side and echoes lines back, simulating
    a device that responds to commands."""

    def __init__(self) -> None:
        self.master_fd, self.slave_fd = pty.openpty()
        self.device_path = Path(os.ttyname(self.slave_fd))
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._echo_loop, daemon=True)
        self._thread.start()

    def _echo_loop(self) -> None:
        """Read from master and echo a fake response back."""
        buf = b''
        while not self._stop.is_set():
            try:
                data = os.read(self.master_fd, 1024)
                if not data:
                    break
                buf += data
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    cmd = line.decode('utf-8', errors='replace').strip()
                    if cmd:
                        response = f'[device] ACK: {cmd}\n'
                        os.write(self.master_fd, response.encode('utf-8'))
            except OSError:
                break

    def close(self) -> None:
        self._stop.set()
        for fd in (self.master_fd, self.slave_fd):
            try:
                os.close(fd)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    _kill_port(DEMO_PORT)

    fake_device = FakeSerialDevice()
    print(f'🔌 Fake serial device at: {fake_device.device_path}')

    # --- Start server (retry in case the OS hasn't fully released the port) ---
    print(f'🚀 Starting CerealServer on {SERVER_ADDRESS}:{DEMO_PORT} ...')
    server = None
    for attempt in range(10):
        try:
            server = CerealServer(
                name='Demo',
                address=SERVER_ADDRESS,
                port=DEMO_PORT,
                device_path=fake_device.device_path,
                output=[sys.stdout],
            )
            break
        except OSError:
            time.sleep(0.5)
    if server is None:
        print(f'❌ Could not bind to port {DEMO_PORT} after retries. Is something else using it?')
        fake_device.close()
        sys.exit(1)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    print('✅ Server online\n')

    # --- Connect client ---
    print('🔗 Connecting CerealClient ...')
    log_buffer: list[str] = []
    client = CerealClient(
        name='DemoClient',
        address=SERVER_ADDRESS,
        port=DEMO_PORT,
        output=[log_buffer],
        default_annotation_emoji='📡',
    )
    time.sleep(0.5)
    print('✅ Client connected\n')

    # --- Send some commands ---
    commands = [
        'echo hello',
        'uname -a',
        'date',
    ]
    for cmd in commands:
        print(f'➡️  Sending: {cmd}')
        client.send(cmd)
        time.sleep(0.5)

    # --- Send a manual annotation with a different emoji ---
    client.annotate('CUSTOM MARKER', emoji='🔥')
    time.sleep(0.5)

    # --- Done ---
    print('\n📋 Collected log buffer:')
    print('─' * 60)
    for line in log_buffer:
        print(f'  {line}', end='')
    print('─' * 60)

    print('\n🛑 Demo complete.')
    os._exit(0)  # Hard exit — daemon threads hold blocking I/O that stalls interpreter shutdown


if __name__ == '__main__':
    signal.signal(signal.SIGINT, lambda *_: os._exit(0))
    signal.signal(signal.SIGTERM, lambda *_: os._exit(0))
    main()
