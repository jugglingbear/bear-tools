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


def get_ssid_for_interface(interface: str) -> str | None:
    """
    Get the SSID currently joined on a specific Wi-Fi interface

    :param interface: The wireless interface to query (e.g. 'en0', 'en1')
    :return: The SSID joined on `interface` if any; None otherwise
    """

    macos_version: str = platform.mac_ver()[0]
    if macos_version.startswith('14'):
        return get_current_ssid_macos14_and_older(interface=interface)
    return get_current_ssid_macos15(interface=interface)


def get_local_ip_for_ssid(ssid: str, max_interface_index: int = 9) -> str | None:
    """
    Find this Mac's local IPv4 address on the NIC currently joined to a given SSID

    Iterates `en0` through `en<max_interface_index>` looking for an interface that reports the
    requested SSID via `networksetup -getairportnetwork` (or its macOS 15+ equivalent), then
    returns the IPv4 address bound to that interface via `ipconfig getifaddr`.

    :param ssid: The SSID to match against
    :param max_interface_index: Highest `en<N>` index to probe (default 9)
    :return: The IPv4 address as a string if found; None otherwise
    """

    for index in range(max_interface_index + 1):
        interface = f'en{index}'
        if get_ssid_for_interface(interface) != ssid:
            continue
        try:
            output: str = subprocess.check_output(['ipconfig', 'getifaddr', interface]).decode().strip()
        except subprocess.CalledProcessError:
            continue
        if output:
            return output
    return None


if __name__ == '__main__':
    _ssid: str | None = get_current_ssid()
    print(f'ssid: "{_ssid}"')
