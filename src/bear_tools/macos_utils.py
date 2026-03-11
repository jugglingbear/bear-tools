"""
macOS-specific utilities
"""

# TODO: Update to use platform.mac_ver() and have one unified get-ssid API

import platform
import re
import subprocess


def get_current_ssid_macos14_and_older(interface: str = 'en0') -> str | None:
    """
    Get the currently-connected SSID (macOS 14 and older)

    :param interface: The wireless interface to use
    :return: The currently-connected SSID if found; None otherwise
    """

    try:
        output: str = subprocess.check_output(['networksetup', '-getairportnetwork', f'{interface}']).decode()
    except subprocess.CalledProcessError:
        return None

    prefix = 'Current Wi-Fi Network: '
    if prefix in output:
        return output.replace('Current Wi-Fi Network: ', '').strip()
    return None


def get_current_ssid_macos15(interface: str = 'en0') -> str | None:
    """
    Get the currently-connected SSID (macOS 15 and newer)

    Note:
        On newer versions of macOS 15.x, this command requires running the following command once to get set up:
        sudo ipconfig setverbose 1

    Example without setverbose:
        ipconfig getsummary en0 | grep SSID
            BSSID : <redacted>
            SSID : <redacted>

    :param interface: The wireless interface to use
    :return: The currently-connected SSID if found; None otherwise
    """

    try:
        output: str = subprocess.check_output(['ipconfig', 'getsummary', f'{interface}']).decode()
        # Require the captured ASCII token to run right up to the newline.
        # This prevents partial matches like "Caf" from "CaféNet".
        regex: str = r'\n\s+SSID : ([\x20-\x7E]{1,32})(?=\n)'
        match = re.search(regex, output)
        return match.group(1) if match else None
    except subprocess.CalledProcessError:
        return None


def get_current_ssid() -> str | None:
    """
    Get the currently-connected SSID

    :param interface: The wireless interface to use
    :return: The currently-connected SSID if found; None otherwise
    """

    macos_version: str = platform.mac_ver()[0]
    if macos_version.startswith('14'):
        return get_current_ssid_macos14_and_older()
    return get_current_ssid_macos15()


if __name__ == '__main__':
    ssid: str | None = get_current_ssid()
    print(f'ssid: "{ssid}"')
