"""
Common Markdown utilities
"""

from __future__ import annotations

import re


def emoji(value: bool) -> str:
    """
    Convert a True/False value into ✅/❌ for visual aesthetics

    :param value: A boolean value
    """

    return '✅' if value else '❌'


def _strip_ansi(s: str) -> str:
    """Remove ANSI escape sequences so visual width can be measured correctly."""
    ansi_re = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_re.sub('', s)


def _display_width(s: str) -> int:
    """Return the number of monospace columns needed to display s.

    Prefers wcwidth.wcswidth when available. If wcwidth is unavailable,
    approximates display width using Unicode East Asian Width and categories:
      * F (Fullwidth) and W (Wide) count as 2 columns
      * Non-spacing marks (Mn), enclosing marks (Me), and format chars (Cf) count as 0
      * All others count as 1
    This covers common cases including emoji and CJK.
    """
    try:
        from wcwidth import wcswidth  # type: ignore
    except Exception:
        # Fallback approximation using stdlib only
        import unicodedata as _ud
        width = 0
        for ch in s:
            cat = _ud.category(ch)
            if cat in ("Mn", "Me", "Cf"):
                continue  # zero-width marks and format characters
            ea = _ud.east_asian_width(ch)
            width += 2 if ea in ("F", "W") else 1
        return width
    else:
        width = wcswidth(s)
        return len(s) if width < 0 else width


def get_table(data: list[list[str]]) -> str:
    """
    Convert a 2D list into a Markdown table with correct alignment for wide Unicode (e.g., emojis).

    Example:
        print(markdown_utils.get_table([
            ['row1col1', 'row1col2'],
            ['row2col1', 'row2col2']
        ]))

        | row1col1 | row1col2 |
        |----------|----------|
        | row2col1 | row2col2 |

    :param data: Two-dimensional string data to convert into a Markdown table
    :return: A string representing the Markdown table.
    """

    if not data or not all(isinstance(_row, list) for _row in data):
        raise ValueError("Input should be a list[list[str]]")

    # Normalize rows: convert values to str and make all rows the same length
    max_cols = max((len(row) for row in data), default=0)
    norm_rows: list[list[str]] = []
    for row in data:
        norm_row = ["" if cell is None else str(cell) for cell in row]
        if len(norm_row) < max_cols:
            norm_row.extend([""] * (max_cols - len(norm_row)))
        norm_rows.append(norm_row)

    # Compute display widths per column using wcwidth when available
    column_widths: list[int] = []
    for col_idx in range(max_cols):
        max_w = 0
        for row in norm_rows:
            text = _strip_ansi(row[col_idx])
            max_w = max(max_w, _display_width(text))
        column_widths.append(max_w)

    # Build rows with manual padding based on display width
    def format_row(row: list[str]) -> str:
        cells: list[str] = []
        for i, raw in enumerate(row):
            text = str(raw)
            disp_w = _display_width(_strip_ansi(text))
            pad = max(column_widths[i] - disp_w, 0)
            cells.append(text + (" " * pad))
        return "| " + " | ".join(cells) + " |"

    table = [format_row(row) for row in norm_rows]
    separator = "|-" + "-|-".join("-" * _w for _w in column_widths) + "-|"

    # Insert the separator after the header row
    table.insert(1, separator)

    return "\n".join(table)
