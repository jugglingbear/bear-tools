# pylint: disable=R0903

from __future__ import annotations

import enum
import platform
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

import netifaces  # type: ignore[import-untyped]

from bear_tools import lumberjack

logger = lumberjack.Logger()

# Note: airport utility is deprecated after macOS 14.4
path_airport = Path('/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport')
path_system_profiler = Path('/usr/sbin/system_profiler')


class SupportedPlatforms:
    """
    A lookup table of supported operating system platforms for this file
    """

    MACOS     = "Darwin"
    WINDOWS = "Windows"
    LINUX   = "Linux"


class WirelessBand:
    """
    Placeholder for Wireless Band types
    """

    BAND_2_4_GHZ = '2.4 GHz'
    BAND_5_GHZ = '5 GHz'
    BAND_UNKNOWN = 'Unknown'


class BluetoothSnifferLogType(enum.Enum):
    """
    Different types of log outputs supported by the sniffer
    """

    RAW = 0
    SIMPLE = 1


    @classmethod
    def get_description(cls, log_type: BluetoothSnifferLogType) -> str:
        """Description of log outputs"""
        if log_type == cls.RAW:
            return (
                'Every time a peripheral advertisement is seen, it is logged.\n'
                'If no advertisement is seen for <MAX ADVERTISEMENT GAP TIME>, it starts logging the fact regularly.'
            )
        if log_type == cls.SIMPLE:
            return (
                'When a peripheral advertisement is seen, the fact is logged.\n'
                'If no peripheral advertisements are seen for <MAX ADVERT. GAP TIME>, the fact is logged.\n'
                'Basically, the logs only contain FOUND/NOT-FOUND transitions'
            )
        return '<NO DESCRIPTION AVAILABLE. BAD DEV. NO DONUT>'


def find_available_port() -> int:
    """
    Get an available port for use as determined by the OS
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))        # 0 -> Let the OS choose
        port: int = s.getsockname()[1]  # Retrieve the port number
        return port


def find_ip_addresses(regex: str, address_family: int = socket.AF_INET) -> list[str]:
    """
    Get a list of IP addresses associated with the current network that match the given regular expression

    :param regex: A regular expression to match an IP address(es) (e.g. r'192.168.1.[0-9]+')
    :param address_family: Indicates the address family (e.g. AF_INET --> IPv4)
    :return:
    """

    ip_addresses: list[str] = []

    interface: str
    for interface in netifaces.interfaces():
        all_addresses: dict[int, list[dict[str, Any]]] = netifaces.ifaddresses(interface)

        address: dict[str, str]
        for address in all_addresses.get(address_family, []):
            ip_address: str | None = address.get('addr')
            if ip_address is not None and re.match(regex, ip_address) is not None:
                ip_addresses.append(ip_address)

    return sorted(list(set(ip_addresses)))


def get_wireless_band() -> str:
    """
    Get the wireless band for the currently-connected wireless network

    2.4 GHz / 5 GHz channel range source:
        https://www.radio-electronics.com/info/wireless/wi-fi/80211-channels-number-frequencies-bandwidth.php

    Note: Using system_profiler since Apple deprecated airport after macOS 14.4

    :return: Wireless band represented in human-readable string form (e.g. "2.4 GHz" or "5 GHz")
    """

    current_platform = platform.system()
    if current_platform == SupportedPlatforms.MACOS:
        if path_system_profiler.exists():
            command = [str(path_system_profiler), 'SPAirPortDataType']
            output = subprocess.check_output(command).decode()
            channel_regex = re.compile('Current Network Information:.*?PHY Mode.*?Channel: ([0-9]+)', re.DOTALL)
            results = channel_regex.findall(output)

            if len(results) == 0:
                logger.error('Failed to determine channel, wireless band')
                return WirelessBand.BAND_UNKNOWN
            channel = int(results[0])

            if 1 <= channel <= 14:
                return WirelessBand.BAND_2_4_GHZ
            else:
                return WirelessBand.BAND_5_GHZ
        else:
            return f'Error: required file not found: {path_system_profiler}'
    else:
        logger.error(f'Platform not supported: {current_platform}')
        return WirelessBand.BAND_UNKNOWN


def is_port_in_use(address: str, port: int) -> bool:
    """
    Determine if a port is in use on the local host

    :param address: The address to check (e.g. 'localhost', '192.168.x.x')
    :param port: The port to check
    :return: True if something was found on the given port and is connectable; False otherwise
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((address, port)) == 0


def scan_for_ssid(ssid: str, timeout_sec: float = 20.0, invert: bool = False) -> bool:
    """
    Determine if the local host can find a specific SSID by name

    :param ssid: The name of the SSID to scan for
    :param timeout_sec: How long to scan (seconds) before giving up (plus duration of one scan, which can take few sec)
    :param invert: If True, verify that the SSID is _not_ found after timeout_sec seconds
    :return: True if the SSID was found (unless invert==True); False otherwise
    """

    current_platform = platform.system()

    if current_platform != SupportedPlatforms.MACOS:
        raise EnvironmentError(f'Platform not supported (yet): {current_platform}')
    if not path_system_profiler.exists():
        raise EnvironmentError(f'{path_system_profiler} not found. Unable to scan for SSIDs')

    ssids: list[str] = []

    logger.info(f'Scanning for SSID: "{ssid}" (timeout: {timeout_sec:.2f} seconds)')
    start_time = time.perf_counter()
    while time.perf_counter() - start_time <= timeout_sec:
        output: bytes = subprocess.check_output([str(path_system_profiler), 'SPAirPortDataType'])
        text: str = output.decode()
        regex = re.compile(r'\n\s+([\x20-\x7E]{1,32}):\n\s+PHY Mode:')  # 0x20...0x7E --> ASCII for printable characters
        for _ssid in sorted(list(set(regex.findall(text)))):
            if _ssid not in ssids:
                ssids.append(_ssid)
            if not invert and ssid in ssids:
                return True
        logger.debug(f'Scanning... ssids found: {sorted(ssids)}')

    return invert


def wait_for_server(address: str, port: int, timeout_sec: float = 10.0) -> bool:
    """
    Wait for a server to be connectable

    :param address: The address of the server
    :param port: The port on which the server is (hopefully) running
    :param timeout_sec: How long to wait (seconds) before giving up
    :return: True if the server was found and is discoverable; False otherwise
    """

    start_time: float = time.perf_counter()
    while time.perf_counter() - start_time <= timeout_sec:
        if is_port_in_use(address, port):
            return True
    return False


def wait_for_server_offline(address: str, port: int, timeout_sec: float = 10.0, poll_sec: float = 0.500) -> bool:
    """
    Wait for a given server to be offline (i.e. unavailable, not connectable)

    :param address: The address of the server
    :param port: The port of the server
    :param timeout_sec: How long to wait (seconds) before giving up
    :param poll_sec: How long to wait between each query
    :return: True if the server if offline; False otherwise
    """

    start_time = time.perf_counter()
    while time.perf_counter() - start_time <= timeout_sec:
        if not is_port_in_use(address, port):
            return True
        time.sleep(poll_sec)
    return False
