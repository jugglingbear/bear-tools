"""
Unit tests for bear_tools.string_utils module
"""

# pylint: disable=C0115,R0903

from typing import Iterator
from unittest.mock import Mock, patch

import pytest

from bear_tools.string_utils import bytearray2str, get_aligned_text, remove_control_chars


class TestBytearrayToStr:
    """Test cases for bytearray2str function."""

    def test_none_input(self) -> None:
        """Test that None input returns None."""
        assert bytearray2str(None) is None

    def test_empty_list_input(self) -> None:
        """Test that empty list returns '<no data>'."""
        assert bytearray2str([]) == '<no data>'

    def test_bytearray_input_simple_hex(self) -> None:
        """Test bytearray input with simple_hex=True."""
        data = bytearray([0x01, 0x02, 0xFF, 0xAB])
        result = bytearray2str(data, simple_hex=True)
        assert result == "0102FFAB"

    def test_bytearray_input_colon_separated(self) -> None:
        """Test bytearray input with simple_hex=False (default)."""
        data = bytearray([0x01, 0x02, 0xFF, 0xAB])
        result = bytearray2str(data, simple_hex=False)
        assert result == "01:02:FF:AB"

    def test_bytes_input_simple_hex(self) -> None:
        """Test bytes input with simple_hex=True."""
        data = b'\x01\x02\xFF\xAB'
        result = bytearray2str(data, simple_hex=True)
        assert result == "0102FFAB"

    def test_bytes_input_colon_separated(self) -> None:
        """Test bytes input with simple_hex=False."""
        data = b'\x01\x02\xFF\xAB'
        result = bytearray2str(data, simple_hex=False)
        assert result == "01:02:FF:AB"

    def test_string_input_simple_hex(self) -> None:
        """Test string input converted to UTF-8 bytes with simple_hex=True."""
        data = "Hello"
        result = bytearray2str(data, simple_hex=True)
        # "Hello" in UTF-8: H=0x48, e=0x65, l=0x6C, l=0x6C, o=0x6F
        assert result == "48656C6C6F"

    def test_string_input_colon_separated(self) -> None:
        """Test string input converted to UTF-8 bytes with simple_hex=False."""
        data = "Hi"
        result = bytearray2str(data, simple_hex=False)
        # "Hi" in UTF-8: H=0x48, i=0x69
        assert result == "48:69"

    def test_unicode_string_input(self) -> None:
        """Test Unicode string input."""
        data = "héllo"
        result = bytearray2str(data, simple_hex=True)
        # Should handle UTF-8 encoding properly
        expected = bytearray(data.encode('utf-8'))
        expected_hex = ''.join([f'{byte:>02X}' for byte in expected])
        assert result == expected_hex

    def test_single_byte_input(self) -> None:
        """Test single byte input."""
        data = bytearray([0x00])
        result = bytearray2str(data, simple_hex=True)
        assert result == "00"

    def test_single_byte_max_value(self) -> None:
        """Test single byte with maximum value."""
        data = bytearray([0xFF])
        result = bytearray2str(data, simple_hex=False)
        assert result == "FF"

    def test_empty_bytearray(self) -> None:
        """Test empty bytearray."""
        data = bytearray()
        result = bytearray2str(data, simple_hex=True)
        assert result == ""

    def test_empty_bytes(self) -> None:
        """Test empty bytes."""
        data = b''
        result = bytearray2str(data, simple_hex=False)
        assert result == ""

    def test_empty_string(self) -> None:
        """Test empty string."""
        data = ""
        result = bytearray2str(data, simple_hex=True)
        assert result == ""

    def test_special_object_with_successful_typecast(self) -> None:
        """Test special object that can be typecast to bytearray."""
        class ByteLike:
            def __iter__(self) -> Iterator[int]:
                return iter([0x01, 0x02, 0x03])

        mock_data = ByteLike()
        result = bytearray2str(mock_data, simple_hex=True)  # type: ignore[arg-type]
        assert result == "010203"

    def test_special_object_with_failed_typecast(self) -> None:
        """Test special object that cannot be typecast to bytearray."""
        mock_data = Mock()
        mock_data.__iter__ = Mock(side_effect=TypeError("Cannot convert"))
        
        with pytest.raises(TypeError, match=r"Failed to convert data.*to a bytearray"):
            bytearray2str(mock_data)

    def test_hex_formatting_padding(self) -> None:
        """Test that hex values are properly zero-padded."""
        data = bytearray([0x01, 0x0A, 0x10, 0xFF])
        result = bytearray2str(data, simple_hex=True)
        assert result == "010A10FF"
        
        result = bytearray2str(data, simple_hex=False)
        assert result == "01:0A:10:FF"

    def test_large_bytearray(self) -> None:
        """Test with a large bytearray."""
        data = bytearray(range(256))  # 0x00 to 0xFF
        result = bytearray2str(data, simple_hex=True)
        expected = ''.join([f'{i:02X}' for i in range(256)])
        assert result == expected


class TestGetAlignedText:
    """Test cases for get_aligned_text function."""

    def test_empty_input(self) -> None:
        """Test that empty input returns empty list."""
        assert get_aligned_text([]) == []

    def test_single_row_single_column(self) -> None:
        """Test single row with single column."""
        text = [["Hello"]]
        result = get_aligned_text(text)
        expected = [["Hello  "]]  # Default extra_padding=2
        assert result == expected

    def test_single_row_multiple_columns(self) -> None:
        """Test single row with multiple columns."""
        text = [["A", "BB", "CCC"]]
        result = get_aligned_text(text, extra_padding=0)
        expected = [["A  ", "BB ", "CCC"]]  # Last column doesn't get padding
        assert result == expected

    def test_multiple_rows_single_column(self) -> None:
        """Test multiple rows with single column."""
        text = [["A"], ["BB"], ["CCC"]]
        result = get_aligned_text(text)
        # Max width is 3 ("CCC") + 2 padding = 5
        expected = [["A    "], ["BB   "], ["CCC  "]]
        assert result == expected

    def test_multiple_rows_multiple_columns(self) -> None:
        """Test multiple rows with multiple columns."""
        text = [
            ["Name", "Age", "City"],
            ["John", "25", "New York"],
            ["Alice", "30", "LA"]
        ]
        result = get_aligned_text(text)
        # Column widths: "Alice"=5+2=7, "Age"=3+2=5, "New York"=8+2=10
        expected = [
            ["Name   ", "Age  ", "City      "],
            ["John   ", "25   ", "New York  "],
            ["Alice  ", "30   ", "LA        "]
        ]
        assert result == expected

    def test_custom_extra_padding(self) -> None:
        """Test with custom extra_padding."""
        text = [["A", "B"], ["CC", "DD"]]
        result = get_aligned_text(text, extra_padding=1)
        # Column widths: "CC"=2+1=3, "DD"=2+1=3
        expected = [["A  ", "B  "], ["CC ", "DD "]]
        assert result == expected

    def test_zero_extra_padding(self) -> None:
        """Test with zero extra_padding."""
        text = [["A", "BB"], ["CC", "D"]]
        result = get_aligned_text(text, extra_padding=0)
        # Column widths: "CC"=2+0=2, "BB"=2+0=2
        expected = [["A ", "BB"], ["CC", "D "]]
        assert result == expected

    def test_negative_extra_padding(self) -> None:
        """Test with negative extra_padding (edge case)"""
        text = [["ABC", "D"]]
        with pytest.raises(ValueError, match=r'Expected: extra_padding is a non-negative integer, got .*'):
            get_aligned_text(text, extra_padding=-1)

    def test_mixed_column_lengths(self) -> None:
        """Test with varying column lengths."""
        text = [
            ["Short", "Medium Length", "X"],
            ["A", "B", "Very Long Text"],
            ["Med", "C", "Y"]
        ]
        result = get_aligned_text(text)
        # Column widths: "Short"=5+2=7, "Medium Length"=13+2=15, "Very Long Text"=14+2=16
        expected = [
            ["Short  ", "Medium Length  ", "X               "],
            ["A      ", "B              ", "Very Long Text  "],
            ["Med    ", "C              ", "Y               "]
        ]
        assert result == expected

    def test_empty_strings_in_cells(self) -> None:
        """Test with empty strings in some cells."""
        text = [["", "B"], ["A", ""]]
        result = get_aligned_text(text)
        # Column widths: "A"=1+2=3, "B"=1+2=3
        expected = [["   ", "B  "], ["A  ", "   "]]
        assert result == expected

    def test_all_empty_strings(self) -> None:
        """Test with all empty strings."""
        text = [["", ""], ["", ""]]
        result = get_aligned_text(text)
        # Column widths: ""=0+2=2, ""=0+2=2
        expected = [["  ", "  "], ["  ", "  "]]
        assert result == expected

    def test_original_text_unchanged(self) -> None:
        """Test that original text is not modified (deepcopy behavior)."""
        original_text = [["A", "B"], ["C", "D"]]
        original_copy = [row[:] for row in original_text]  # Make a copy for comparison
        
        result = get_aligned_text(original_text)
        
        # Original should be unchanged
        assert original_text == original_copy
        # Result should be different
        assert result != original_text

    def test_unicode_characters(self) -> None:
        """Test with Unicode characters."""
        text = [["ñoño", "café"], ["test", "naïve"]]
        result = get_aligned_text(text)
        # Python len() counts Unicode characters properly
        # Column widths: "test"=4+2=6, "naïve"=5+2=7
        expected = [["ñoño  ", "café   "], ["test  ", "naïve  "]]
        assert result == expected


class TestRemoveControlChars:
    """Test cases for remove_control_chars function."""

    def test_empty_string(self) -> None:
        """Test empty string input."""
        assert remove_control_chars("") == ""

    def test_string_without_control_chars(self) -> None:
        """Test string with no control characters."""
        text = "Hello, World! 123 ABC xyz"
        assert remove_control_chars(text) == text

    def test_string_with_basic_control_chars(self) -> None:
        """Test string with basic control characters."""
        text = "Hello\x00World\x01Test\x1F"
        result = remove_control_chars(text)
        assert result == "HelloWorldTest"

    def test_string_with_tab_and_newline(self) -> None:
        """Test string with TAB and newline characters (should be removed)."""
        text = "Hello\tWorld\nTest\r\n"
        result = remove_control_chars(text)
        assert result == "HelloWorldTest"

    def test_string_with_del_character(self) -> None:
        """Test string with DEL character (0x7F)."""
        text = "Hello\x7FWorld"
        result = remove_control_chars(text)
        assert result == "HelloWorld"

    def test_string_with_all_control_chars(self) -> None:
        """Test string with all control characters (0x00-0x1F and 0x7F)."""
        # Create a string with all control characters
        control_chars = ''.join(chr(i) for i in range(32)) + chr(127)
        text = f"Start{control_chars}End"
        result = remove_control_chars(text)
        assert result == "StartEnd"

    def test_string_with_only_control_chars(self) -> None:
        """Test string containing only control characters."""
        text = "\x00\x01\x02\x03\x1F\x7F"
        result = remove_control_chars(text)
        assert result == ""

    def test_string_with_printable_special_chars(self) -> None:
        """Test that printable special characters are preserved."""
        text = "Hello! @#$%^&*()_+-=[]{}|;':\",./<>?"
        result = remove_control_chars(text)
        assert result == text

    def test_string_with_unicode_characters(self) -> None:
        """Test that Unicode characters are preserved."""
        text = "Héllo Wörld! 你好 🌍"
        result = remove_control_chars(text)
        assert result == text

    def test_string_with_space_character(self) -> None:
        """Test that space character (0x20) is preserved."""
        text = "Hello World"
        result = remove_control_chars(text)
        assert result == text

    def test_string_with_mixed_content(self) -> None:
        """Test string with mixed content including control chars."""
        text = "Line1\nLine2\tTabbed\x00NullByte\x1FUnitSeparator End"
        result = remove_control_chars(text)
        assert result == "Line1Line2TabbedNullByteUnitSeparator End"

    def test_control_chars_boundary_values(self) -> None:
        """Test boundary values for control characters."""
        # Test characters around the control character ranges
        text = "\x1F\x20\x7E\x7F\x80"  # 0x1F (control), 0x20 (space), 0x7E (~), 0x7F (DEL), 0x80 (extended)
        result = remove_control_chars(text)
        # Should remove 0x1F and 0x7F, keep 0x20, 0x7E, and 0x80
        assert result == " ~\x80"

    def test_carriage_return_line_feed(self) -> None:
        """Test specific handling of CRLF sequences."""
        text = "Line1\r\nLine2\rLine3\nLine4"
        result = remove_control_chars(text)
        assert result == "Line1Line2Line3Line4"

    def test_form_feed_and_vertical_tab(self) -> None:
        """Test form feed and vertical tab characters."""
        text = "Page1\fPage2\vVertical"
        result = remove_control_chars(text)
        assert result == "Page1Page2Vertical"

    def test_escape_sequences(self) -> None:
        """Test various escape sequences."""
        text = "Text\a\b\x1bMore"  # Bell (\a), backspace (\b), escape (\x1b) chars
        result = remove_control_chars(text)
        assert result == "TextMore"

    def test_large_string_performance(self) -> None:
        """Test performance with a large string containing control characters."""
        # Create a large string with control characters interspersed
        large_text = ""
        for i in range(1000):
            large_text += f"Text{i}\x00\x01\x02"
        
        result = remove_control_chars(large_text)
        
        # Should have removed all control characters but kept the text
        expected = "".join(f"Text{i}" for i in range(1000))
        assert result == expected

    def test_translation_table_correctness(self) -> None:
        """Test that the translation table is constructed correctly."""
        # This test verifies the internal logic of the function
        text = "".join(chr(i) for i in range(256))  # All possible byte values
        result = remove_control_chars(text)
        
        # Should remove chars 0-31 and 127, keep everything else
        expected = ""
        for i in range(256):
            if not (0 <= i <= 31 or i == 127):
                expected += chr(i)
        
        assert result == expected


# Integration tests and edge cases
class TestStringFunctionsIntegration:
    """Integration tests and additional edge cases."""

    def test_bytearray2str_with_firmware_version_pattern(self) -> None:
        """Test bytearray2str with data that could look like firmware version."""
        # Create bytes that when converted to string might match firmware pattern
        data = b'HD8.01.02.03.04'
        result = bytearray2str(data, simple_hex=False)
        # Should be hex representation, not the string content
        expected = ':'.join([f'{byte:02X}' for byte in data])
        assert result == expected

    def test_get_aligned_text_with_control_characters(self) -> None:
        """Test get_aligned_text with text containing control characters."""
        text = [["Normal", "With\tTab"], ["With\nNewline", "Regular"]]
        result = get_aligned_text(text)
        
        # Should align based on actual string length including control chars
        # "With\nNewline" is longest at 12 chars
        assert len(result[1][0]) > len("Normal")  # Should be padded
        assert "\n" in result[1][0]  # Control char should be preserved

    def test_remove_control_chars_with_aligned_text(self) -> None:
        """Test remove_control_chars used with get_aligned_text output."""
        text = [["Line1\nContinued", "Short"], ["Normal", "Text\tTabbed"]]
        aligned = get_aligned_text(text)
        
        # Clean control chars from aligned text
        cleaned = [[remove_control_chars(cell) for cell in row] for row in aligned]
        
        # Should have removed control chars but preserved padding
        assert "\n" not in cleaned[0][0]
        assert "\t" not in cleaned[1][1]
        # But padding spaces should remain
        assert cleaned[0][1].endswith("  ")  # Should still have padding spaces


if __name__ == "__main__":
    pytest.main([__file__])
