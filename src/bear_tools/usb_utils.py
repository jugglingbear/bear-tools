from __future__ import annotations

import platform
import re
import subprocess
from pathlib import Path

from bear_tools import lumberjack

logger = lumberjack.Logger()

_IOREG_TIMEOUT_SEC = 15.0
_LINUX_USB_DEVICES = Path('/sys/bus/usb/devices')


def get_usb_link_speed_bps(vendor_id: int) -> int | None:
    """
    Get the negotiated USB link speed (bits/sec) of the first connected USB device whose USB-IF vendor id matches
    ``vendor_id``.

    Handy for telling a USB 3.0 "SuperSpeed" link (>= 5_000_000_000 bps) apart from a USB 2.0 "High-Speed" link
    (480_000_000 bps) -- e.g. to detect a slow/bad USB 2.0-only cable.

    Supported hosts:
        - macOS: parsed from ``ioreg`` (``system_profiler SPUSBDataType`` is empty on Apple Silicon)
        - Linux: read from the device ``speed`` (Mbps) in sysfs
        - Any other OS: returns None

    :param vendor_id: The device's USB-IF vendor id (e.g. 0x2672 for GoPro)
    :return: Negotiated link speed in bits/sec, or None if no matching device is found or the speed cannot be determined
             on this host OS
    """

    system = platform.system()
    if system == 'Darwin':
        return _macos_usb_link_speed_bps(vendor_id)
    if system == 'Linux':
        return _linux_usb_link_speed_bps(vendor_id)
    logger.debug(f'get_usb_link_speed_bps is unsupported on host OS "{system}"')
    return None


def _macos_usb_link_speed_bps(vendor_id: int) -> int | None:
    """Read a matching USB device's negotiated link speed (bits/sec) from macOS ``ioreg``."""

    try:
        output = subprocess.run(
            ['ioreg', '-rc', 'IOUSBHostDevice', '-l', '-w0'],
            capture_output=True, text=True, timeout=_IOREG_TIMEOUT_SEC, check=False,
        ).stdout
    except (subprocess.SubprocessError, OSError) as error:
        logger.debug(f'ioreg query failed: {error}')
        return None

    # ioreg lists each USB device node followed by its properties. "UsbLinkSpeed" (bits/sec) is a per-device property
    # and "idVendor" is reported in decimal. Track the most recent link speed and return it once the matching vendor id
    # appears within the same device block.
    link_bps: int | None = None
    for line in output.splitlines():
        if '<class IOUSBHostDevice' in line:            # entering a new device node
            link_bps = None
        elif '"UsbLinkSpeed" =' in line:
            digits = re.search(r'\d+', line.rsplit('=', 1)[-1])
            if digits:
                link_bps = int(digits.group())
        elif f'"idVendor" = {vendor_id}' in line and link_bps is not None:
            return link_bps
    return None


def _linux_usb_link_speed_bps(vendor_id: int) -> int | None:
    """Read a matching USB device's negotiated link speed (bits/sec) from Linux sysfs."""

    for vendor_file in _LINUX_USB_DEVICES.glob('*/idVendor'):
        try:
            if int(vendor_file.read_text().strip(), 16) != vendor_id:
                continue
            speed_mbps = float((vendor_file.parent / 'speed').read_text().strip())
        except (OSError, ValueError):
            continue
        return int(speed_mbps * 1_000_000)
    return None
