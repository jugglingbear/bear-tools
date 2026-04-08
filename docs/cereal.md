# Cereal

**TCP-based serial device server/client for shared serial I/O.**

Cereal lets multiple clients share a single serial device through a central TCP server.
The server reads from a serial device and broadcasts log lines to all connected clients;
any client can send commands back through the server to the device.

## Architecture

```
┌─────────────┐
│ Serial      │
│ Device      │◄──── pyserial ────┐
│ (/dev/...)  │                   │
└─────────────┘            ┌──────┴──────┐
                           │ CerealServer│
                           │  (TCP)      │
                           └──┬───┬───┬──┘
                              │   │   │
                    ┌─────────┘   │   └─────────┐
                    ▼             ▼              ▼
              CerealClient  CerealClient  CerealClient
              (Thread)      (Thread)      (Thread)
```

### Components

| Module | Purpose |
|--------|---------|
| `server.py` | `CerealServer` — `ThreadingTCPServer` that bridges serial ↔ TCP. Handles command relay, log broadcasting, annotation banners, and config queries. |
| `client.py` | `CerealClient` — Threaded TCP client. Receives serial logs, sends commands, supports configurable annotation emojis. |
| `serial_manager.py` | `SerialManager` — pyserial wrapper with timestamped reads, command queuing, and a listener/observer pattern. |
| `tokenizer.py` | `Tokenizer` — Reassembles byte streams into complete messages using a sentinel delimiter. |
| `mods/base.py` | `LoggingModBase` — ABC for writing mods that react to serial log content in real time. |

## Quick Start

### 1. Start a server

```python
from pathlib import Path
from bear_tools.cereal.server import CerealServer
import sys, threading

server = CerealServer(
    name='MyDevice',
    address='localhost',
    port=14441,
    device_path=Path('/dev/cu.usbserial-1400'),
    output=[sys.stdout],
)
threading.Thread(target=server.serve_forever, daemon=True).start()
```

### 2. Connect a client

```python
from bear_tools.cereal.client import CerealClient

client = CerealClient(
    name='MyClient',
    address='localhost',
    port=14441,
    output=[sys.stdout],
)
```

### 3. Send commands and annotate

```python
# Send a command to the serial device (auto-annotated with 📡)
client.send('echo hello')

# Send a manual annotation with a custom emoji
client.annotate('TEST START', emoji='🧪')

# Disconnect
client.stop()
```

## Annotations

Annotations inject visible banners into the log stream, making it easy to find boundaries
(test start/end, manual markers, command sends) when reviewing logs.

### How it works

1. `client.send(text)` automatically annotates before sending:
   ```
   📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡 SENDING: echo hello 📡📡📡📡📡📡📡📡📡📡📡📡📡📡📡
   ```

2. `client.annotate(text, emoji='🔥')` sends a standalone annotation:
   ```
   🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥 TEST START 🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
   ```

### Default emoji

The default annotation emoji is set per-client via the constructor:

```python
# All annotations use 📡 unless overridden per-call
client = CerealClient(..., default_annotation_emoji='📡')

# Override for a specific annotation
client.annotate('TEST START', emoji='🧪')
```

### Protocol

Annotations are sent as a special command over the wire:

```
__annotate:<emoji>:<text>
```

The server parses this and broadcasts the banner to all connected clients via `notify_listeners()`.

## SerialManager

`SerialManager` handles the low-level serial I/O. It runs a read loop on a background thread
and notifies registered listeners whenever new data arrives.

```python
from bear_tools.cereal.serial_manager import SerialManager, SerialListener

class MyListener(SerialListener):
    @property
    def name(self) -> str:
        return 'my-listener'

    def handle_event(self, event: str) -> None:
        print(f'Got: {event}')

mgr = SerialManager('MyDevice', '/dev/cu.usbserial-1400', start=True)
mgr.register_listener(MyListener())
mgr.queue_command('echo hello')
```

### Command aliases

`SerialManager.queue_command()` supports aliases — shorthand names that expand to longer
commands. Register them in `COMMAND_ALIASES`:

```python
mgr.COMMAND_ALIASES['__reboot'] = 'sudo reboot'
mgr.queue_command('__reboot')  # sends "sudo reboot" to the device
```

## Tokenizer

The `Tokenizer` reassembles a byte stream into discrete messages using a sentinel delimiter.
TCP doesn't guarantee message boundaries, so the tokenizer buffers partial data until a
complete sentinel-terminated message arrives.

```python
from bear_tools.cereal.tokenizer import Tokenizer

tok = Tokenizer(sentinel=b'\x00\x00\x00')
tok.add(b'hello\x00\x00\x00wor')
tok.add(b'ld\x00\x00\x00')
print(tok.tokens)  # [b'hello', b'world']
```

## Logging Mods

Subclass `LoggingModBase` to create mods that react to serial log content:

```python
from bear_tools.cereal.mods.base import LoggingModBase

class WatchdogMod(LoggingModBase):
    @property
    def name(self) -> str:
        return 'watchdog'

    def process(self, line: str) -> None:
        if 'PANIC' in line:
            print(f'🚨 Device panic detected!')
```

Register mods when creating a client:

```python
client = CerealClient(..., mods=[WatchdogMod()])
```

## Demo

A self-contained demo that uses a pseudo-terminal instead of real hardware:

```bash
poetry run python3 samples/cereal/demo.py
```

See [`samples/cereal/demo.py`](../samples/cereal/demo.py) for the full source.
