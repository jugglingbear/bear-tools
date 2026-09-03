from __future__ import annotations

import platform
from unittest import mock

from bear_tools import usb_utils

_GOPRO_VENDOR_ID = 0x2672  # 9842 decimal

_IOREG_SAMPLE = (
    '  +-o USB2.0 Hub@0  <class IOUSBHostDevice, id 0x1>\n'
    '        "UsbLinkSpeed" = 480000000\n'
    '        "idVendor" = 1234\n'
    '  +-o MISSION 1 PRO ILS@1  <class IOUSBHostDevice, id 0x2>\n'
    '        "UsbLinkSpeed" = 5000000000\n'
    '        "idVendor" = 9842\n'
)


def test_unsupported_os_returns_none() -> None:
    with mock.patch.object(platform, 'system', return_value='Windows'):
        assert usb_utils.get_usb_link_speed_bps(_GOPRO_VENDOR_ID) is None


def test_macos_returns_matching_vendor_link_speed() -> None:
    with mock.patch.object(platform, 'system', return_value='Darwin'), \
         mock.patch.object(usb_utils.subprocess, 'run', return_value=mock.Mock(stdout=_IOREG_SAMPLE)):
        assert usb_utils.get_usb_link_speed_bps(_GOPRO_VENDOR_ID) == 5_000_000_000


def test_macos_unknown_vendor_returns_none() -> None:
    with mock.patch.object(platform, 'system', return_value='Darwin'), \
         mock.patch.object(usb_utils.subprocess, 'run', return_value=mock.Mock(stdout=_IOREG_SAMPLE)):
        assert usb_utils.get_usb_link_speed_bps(0xDEAD) is None
