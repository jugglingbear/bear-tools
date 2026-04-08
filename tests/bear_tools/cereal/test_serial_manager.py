"""Unit tests for bear_tools.cereal.serial_manager module."""

from bear_tools.cereal.serial_manager import (
    PrintColor,
    SerialClient,
    SerialListener,
    SerialManager,
    get_timestamp,
)


class TestGetTimestamp:
    """Test the get_timestamp utility."""

    def test_format(self) -> None:
        """Timestamp has expected format: [YYYY-MM-DD HH:MM:SS.mmm]."""
        ts = get_timestamp()
        # Should be like '2026-04-07 12:34:56.789'
        assert len(ts) == 23
        assert ts[4] == '-'
        assert ts[7] == '-'
        assert ts[10] == ' '
        assert ts[13] == ':'
        assert ts[16] == ':'
        assert ts[19] == '.'

    def test_millisecond_precision(self) -> None:
        """Timestamp has exactly 3 digits of sub-second precision."""
        ts = get_timestamp()
        ms_part = ts.split('.')[-1]
        assert len(ms_part) == 3


class TestPrintColor:
    """Test PrintColor ANSI codes."""

    def test_color_off_resets(self) -> None:
        assert PrintColor.COLOR_OFF == '\033[0m'

    def test_colors_are_escape_sequences(self) -> None:
        for attr in ['BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'PURPLE', 'CYAN', 'WHITE']:
            value = getattr(PrintColor, attr)
            assert value.startswith('\033[')


class ConcreteListener(SerialListener):
    """Concrete implementation of SerialListener for testing."""

    def __init__(self, name: str = 'test-listener'):
        self._name = name
        self.events: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    def handle_event(self, event: str) -> None:
        self.events.append(event)


class TestSerialManagerListeners:
    """Test listener registration and notification without a real serial device."""

    def _make_manager(self) -> SerialManager:
        """Create a SerialManager that is NOT started (no serial device needed)."""
        return SerialManager(name='test', device_path='/dev/null', start=False)

    def test_register_listener(self) -> None:
        mgr = self._make_manager()
        listener = ConcreteListener()
        mgr.register_listener(listener)
        assert listener in mgr.listeners

    def test_unregister_listener(self) -> None:
        mgr = self._make_manager()
        listener = ConcreteListener()
        mgr.register_listener(listener)
        mgr.unregister_listener(listener)
        assert listener not in mgr.listeners

    def test_unregister_missing_listener_no_error(self) -> None:
        """Unregistering a listener that was never added does not raise."""
        mgr = self._make_manager()
        listener = ConcreteListener()
        mgr.unregister_listener(listener)  # should be a no-op

    def test_notify_listeners(self) -> None:
        mgr = self._make_manager()
        listener1 = ConcreteListener('l1')
        listener2 = ConcreteListener('l2')
        mgr.register_listener(listener1)
        mgr.register_listener(listener2)

        mgr.notify_listeners('test event\n')
        assert listener1.events == ['test event\n']
        assert listener2.events == ['test event\n']

    def test_notify_filters_none_listeners(self) -> None:
        """None entries in the listener list are pruned during notification."""
        mgr = self._make_manager()
        listener = ConcreteListener()
        mgr.register_listener(listener)
        mgr.listeners.append(None)  # simulate stale entry

        mgr.notify_listeners('event\n')
        assert listener.events == ['event\n']
        assert None not in mgr.listeners


class TestSerialManagerCommandQueue:
    """Test command queue operations."""

    def test_queue_command(self) -> None:
        mgr = SerialManager(name='test', device_path='/dev/null', start=False)
        mgr.queue_command('echo hello')
        assert mgr.command_queue == ['echo hello']

    def test_queue_multiple_commands(self) -> None:
        mgr = SerialManager(name='test', device_path='/dev/null', start=False)
        mgr.queue_command('cmd1')
        mgr.queue_command('cmd2')
        assert mgr.command_queue == ['cmd1', 'cmd2']

    def test_command_queue_returns_copy(self) -> None:
        """command_queue property returns a copy, not the internal list."""
        mgr = SerialManager(name='test', device_path='/dev/null', start=False)
        mgr.queue_command('cmd')
        queue = mgr.command_queue
        queue.clear()
        assert mgr.command_queue == ['cmd']  # internal list unaffected


class TestSerialManagerStop:
    """Test stop signal."""

    def test_stop_sets_event(self) -> None:
        mgr = SerialManager(name='test', device_path='/dev/null', start=False)
        mgr.stop()
        # The stop event should be set (thread would exit its loop)
        assert mgr._SerialManager__stop_event.is_set()


class TestSerialClientBasic:
    """Test SerialClient without a real serial connection."""

    def test_handle_event_stores_output(self) -> None:
        client = SerialClient(name='test')
        client.handle_event('hello world\n')
        assert 'hello world' in client.command_output

    def test_handle_event_accumulates(self) -> None:
        client = SerialClient(name='test')
        client.handle_event('line1\n')
        client.handle_event('line2\n')
        assert 'line1' in client.command_output
        assert 'line2' in client.command_output

    def test_name_property(self) -> None:
        client = SerialClient(name='my-client')
        assert client.name == 'my-client'

    def test_rejects_unprintable_command(self) -> None:
        client = SerialClient(name='test', silent=True)
        result = client.send_command('\x00\x01\x02', expect_output=False)
        assert result is None
