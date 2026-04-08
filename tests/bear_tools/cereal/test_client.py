"""Unit tests for bear_tools.cereal.client module."""

import os

from bear_tools import cereal
from bear_tools.cereal.client import CerealClient


class TestCerealClientPipeLifecycle:
    """Test that pipe file descriptors are properly managed."""

    def _make_client(self, **kwargs) -> CerealClient:
        """Create a CerealClient that does not auto-start (no server needed)."""
        defaults = dict(name='test', address='localhost', port=19999, output=[], mods=[], start=False)
        defaults.update(kwargs)
        return CerealClient(**defaults)

    def test_pipes_created_on_init(self) -> None:
        """Pipe FDs are valid after construction."""
        client = self._make_client()
        assert client.command_pipe_read >= 0
        assert client.command_pipe_write >= 0
        assert client.message_pipe_read >= 0
        assert client.message_pipe_write >= 0
        client._close_pipes()

    def test_close_pipes_idempotent(self) -> None:
        """Calling _close_pipes multiple times does not raise."""
        client = self._make_client()
        client._close_pipes()
        client._close_pipes()  # second call should be a no-op

    def test_close_pipes_actually_closes_fds(self) -> None:
        """After _close_pipes, the FDs are no longer valid."""
        import pytest
        client = self._make_client()
        fds = [
            client.command_pipe_read,
            client.command_pipe_write,
            client.message_pipe_read,
            client.message_pipe_write,
        ]
        client._close_pipes()
        for fd in fds:
            with pytest.raises(OSError):
                os.fstat(fd)

    def test_stop_on_non_started_client(self) -> None:
        """Calling stop() on a client that was never started doesn't raise."""
        client = self._make_client()
        client.stop()  # should be a no-op since thread was never started
        client._close_pipes()


class TestCerealClientMessageFraming:
    """Test that _send_raw() properly frames messages with END_OF_MESSAGE sentinel."""

    def _make_client(self, **kwargs) -> CerealClient:
        defaults = dict(name='test', address='localhost', port=19999, output=[], mods=[], start=False)
        defaults.update(kwargs)
        return CerealClient(**defaults)

    def test_send_raw_writes_framed_message_to_pipe(self) -> None:
        """_send_raw() writes the message + END_OF_MESSAGE sentinel to the message pipe."""
        client = self._make_client()

        text = 'test_command'
        client._send_raw(text, expect_output=False)

        data = os.read(client.message_pipe_read, 4096)
        expected = text.encode('utf-8') + cereal.END_OF_MESSAGE
        assert data == expected
        client._close_pipes()

    def test_send_writes_annotation_then_command(self) -> None:
        """send() writes an annotation message followed by the actual command to the pipe."""
        client = self._make_client()

        text = 'my_command'
        client.send(text, expect_output=False)

        # Read all data written to the pipe
        data = os.read(client.message_pipe_read, 8192)

        # Should contain the annotation and the command, both framed with END_OF_MESSAGE
        annotation_prefix = cereal.SERVER_COMMAND_ANNOTATE.encode('utf-8')
        command_bytes = text.encode('utf-8') + cereal.END_OF_MESSAGE

        assert annotation_prefix in data, 'Annotation message not found in pipe data'
        assert data.endswith(command_bytes), 'Command should be the last framed message'
        client._close_pipes()

    def test_send_raw_empty_string(self) -> None:
        """_send_raw() works with an empty command string."""
        client = self._make_client()
        client._send_raw('', expect_output=False)

        data = os.read(client.message_pipe_read, 4096)
        assert data == cereal.END_OF_MESSAGE  # empty payload + sentinel
        client._close_pipes()


class TestCerealClientAnnotation:
    """Test annotation behavior."""

    def _make_client(self, **kwargs) -> CerealClient:
        defaults = dict(name='test', address='localhost', port=19999, output=[], mods=[], start=False)
        defaults.update(kwargs)
        return CerealClient(**defaults)

    def test_default_annotation_emoji(self) -> None:
        """Default annotation emoji is 📡."""
        client = self._make_client()
        assert client.default_annotation_emoji == '📡'
        client._close_pipes()

    def test_custom_default_annotation_emoji(self) -> None:
        """Constructor-provided default_annotation_emoji is stored."""
        client = self._make_client(default_annotation_emoji='🧪')
        assert client.default_annotation_emoji == '🧪'
        client._close_pipes()

    def test_annotate_uses_default_emoji(self) -> None:
        """annotate() with no emoji arg uses the instance default."""
        client = self._make_client(default_annotation_emoji='🔬')
        client.annotate('hello')

        data = os.read(client.message_pipe_read, 4096)
        text = data.decode('utf-8').rstrip('\x00')
        assert '🔬:hello' in text
        client._close_pipes()

    def test_annotate_per_call_emoji_override(self) -> None:
        """annotate() with explicit emoji overrides the instance default."""
        client = self._make_client(default_annotation_emoji='🧪')
        client.annotate('hello', emoji='📡')

        data = os.read(client.message_pipe_read, 4096)
        text = data.decode('utf-8').rstrip('\x00')
        assert '📡:hello' in text
        assert '🧪' not in text
        client._close_pipes()

    def test_annotate_message_has_correct_protocol_prefix(self) -> None:
        """annotate() sends the __annotate: protocol prefix."""
        client = self._make_client()
        client.annotate('test annotation')

        data = os.read(client.message_pipe_read, 4096)
        text = data.decode('utf-8')
        assert cereal.SERVER_COMMAND_ANNOTATE in text
        client._close_pipes()


class TestCerealClientStr:
    """Test __str__ representation."""

    def test_str(self) -> None:
        client = CerealClient(name='rtos', address='10.0.0.1', port=14441, output=[], start=False)
        result = str(client)
        assert 'rtos' in result
        assert '10.0.0.1' in result
        assert '14441' in result
        client._close_pipes()
