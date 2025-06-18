"""
macOS-specific utilities
"""

import re
import subprocess


def get_current_ssid(interface: str = 'en0') -> str | None:
    """
    Get the currently-connected SSID

    :param interface: The wireless interface to use
    :return: The currently-connected SSID if found; None otherwise
    """

    try:
        output: str = subprocess.check_output(['ipconfig', 'getsummary', f'{interface}']).decode()
        regex: str = r'\n\s+SSID : ([\x20-\x7E]{1,32})'
        match = re.search(regex, output)
        return match.group(1) if match else None
    except subprocess.CalledProcessError:
        return None


if __name__ == '__main__':
    ssid: str | None = get_current_ssid()
    print(f'ssid: "{ssid}"')
