"""
Common Markdown utilities
"""


def emoji(value: bool) -> str:
    """
    Convert a True/False value into ✅/❌ for visual aesthetics

    :param value: A boolean value
    """

    return '✅' if value else '❌'


def get_table(data: list[list[str]]) -> str:
    """
    Convert a 2D list into a Markdown table

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

    column_widths: list[int] = [max(len(str(_item)) for _item in _col) for _col in zip(*data)]
    row_template: str = "| " + " | ".join("{:<" + str(width) + "}" for width in column_widths) + " |"
    table = [row_template.format(*row) for row in data]
    separator = "|-" + "-|-".join("-" * _width for _width in column_widths) + "-|"

    # Insert the separator after the header row
    table.insert(1, separator)

    return "\n".join(table)
