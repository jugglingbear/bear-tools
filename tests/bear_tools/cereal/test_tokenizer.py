"""Unit tests for bear_tools.cereal.tokenizer module."""

from bear_tools.cereal.tokenizer import Tokenizer


class TestTokenizer:
    """Test cases for the Tokenizer class."""

    SENTINEL = b'\x00\x00\x00'

    def test_single_complete_message(self) -> None:
        """A single complete message yields one token."""
        t = Tokenizer(self.SENTINEL)
        t.add(b'hello' + self.SENTINEL)
        assert t.tokens == [b'hello']

    def test_multiple_messages_in_one_add(self) -> None:
        """Multiple complete messages in a single add() call yield multiple tokens."""
        t = Tokenizer(self.SENTINEL)
        t.add(b'aaa' + self.SENTINEL + b'bbb' + self.SENTINEL)
        assert t.tokens == [b'aaa', b'bbb']

    def test_partial_message_buffered(self) -> None:
        """Partial messages are buffered until the sentinel arrives."""
        t = Tokenizer(self.SENTINEL)
        t.add(b'hel')
        assert t.tokens == []
        t.add(b'lo' + self.SENTINEL)
        assert t.tokens == [b'hello']

    def test_sentinel_split_across_adds(self) -> None:
        """A sentinel split across two add() calls is still detected."""
        t = Tokenizer(self.SENTINEL)
        t.add(b'data\x00\x00')
        assert t.tokens == []
        t.add(b'\x00')
        assert t.tokens == [b'data']

    def test_empty_add(self) -> None:
        """Adding empty bytes does nothing."""
        t = Tokenizer(self.SENTINEL)
        t.add(b'')
        assert t.tokens == []
        assert len(t.buffer) == 0

    def test_empty_message_between_sentinels(self) -> None:
        """Two adjacent sentinels produce an empty token."""
        t = Tokenizer(self.SENTINEL)
        t.add(self.SENTINEL + self.SENTINEL)
        assert t.tokens == [b'', b'']

    def test_clear_tokens_and_continue(self) -> None:
        """After clearing tokens, subsequent data still works."""
        t = Tokenizer(self.SENTINEL)
        t.add(b'first' + self.SENTINEL)
        assert t.tokens == [b'first']
        t.tokens.clear()
        t.add(b'second' + self.SENTINEL)
        assert t.tokens == [b'second']

    def test_custom_sentinel(self) -> None:
        """Tokenizer works with an arbitrary sentinel value."""
        sentinel = b'END'
        t = Tokenizer(sentinel)
        t.add(b'helloENDworldEND')
        assert t.tokens == [b'hello', b'world']

    def test_large_message(self) -> None:
        """Tokenizer handles messages larger than typical buffer sizes."""
        t = Tokenizer(self.SENTINEL)
        payload = b'x' * 10000
        t.add(payload + self.SENTINEL)
        assert t.tokens == [payload]

    def test_incremental_byte_by_byte(self) -> None:
        """Feeding data one byte at a time still produces the correct token."""
        t = Tokenizer(self.SENTINEL)
        full = b'hello' + self.SENTINEL
        for byte in full:
            t.add(bytes([byte]))
        assert t.tokens == [b'hello']

    def test_buffer_state_after_complete_parse(self) -> None:
        """Buffer is empty after all complete messages are consumed."""
        t = Tokenizer(self.SENTINEL)
        t.add(b'msg' + self.SENTINEL)
        assert len(t.buffer) == 0

    def test_buffer_retains_trailing_partial(self) -> None:
        """Buffer retains trailing data after the last sentinel."""
        t = Tokenizer(self.SENTINEL)
        t.add(b'msg' + self.SENTINEL + b'partial')
        assert t.tokens == [b'msg']
        assert bytes(t.buffer) == b'partial'
