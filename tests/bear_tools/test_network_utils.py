# flake8: noqa: E501
# pylint: disable=C0301,C0115,C0116

from __future__ import annotations

import itertools
import socket
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock, patch

import pytest

from bear_tools import network_utils


def perf_counter_generator(start: float = 0.0, step: float = 0.1) -> Callable[[], float]:
    """
    Returns a callable that mimics time.perf_counter, increasing by step each call.
    """
    counter = itertools.count(start=start, step=step)
    return lambda: next(counter)


class TestBluetoothSnifferLogType:
    def test_get_description(self) -> None:
        assert "Every time" in network_utils.BluetoothSnifferLogType.get_description(network_utils.BluetoothSnifferLogType.RAW)
        assert "FOUND/NOT-FOUND" in network_utils.BluetoothSnifferLogType.get_description(network_utils.BluetoothSnifferLogType.SIMPLE)
        class DummyType:
            pass
        assert "<NO DESCRIPTION" in network_utils.BluetoothSnifferLogType.get_description(DummyType())  # type: ignore[arg-type]


class TestPortUtilities:
    def test_find_available_port(self) -> None:
        port: int = network_utils.find_available_port()
        assert isinstance(port, int)
        assert 0 < port < 65536

    @patch("socket.socket.connect_ex", return_value=0)
    def test_is_port_in_use_true(self, _: MagicMock) -> None:
        assert network_utils.is_port_in_use("localhost", 80) is True

    @patch("socket.socket.connect_ex", return_value=1)
    def test_is_port_in_use_false(self, _: MagicMock) -> None:
        assert network_utils.is_port_in_use("localhost", 9999) is False

    @patch("bear_tools.network_utils.is_port_in_use", side_effect=[False, True])
    @patch("time.perf_counter", side_effect=perf_counter_generator())
    def test_wait_for_server_success(self, _: MagicMock, __: MagicMock) -> None:
        assert network_utils.wait_for_server("localhost", 80, timeout_sec=1.0) is True

    @patch("bear_tools.network_utils.is_port_in_use", return_value=False)
    @patch("time.perf_counter", side_effect=perf_counter_generator())
    def test_wait_for_server_timeout(self, _: MagicMock, __: MagicMock) -> None:
        assert network_utils.wait_for_server("localhost", 80, timeout_sec=0.3) is False

    @patch("bear_tools.network_utils.is_port_in_use", side_effect=[True, False])
    @patch("time.perf_counter", side_effect=perf_counter_generator())
    def test_wait_for_server_offline_success(self, _: MagicMock, __: MagicMock) -> None:
        assert network_utils.wait_for_server_offline("localhost", 80, timeout_sec=1.0) is True

    @patch("bear_tools.network_utils.is_port_in_use", return_value=True)
    @patch("time.perf_counter", side_effect=perf_counter_generator())
    def test_wait_for_server_offline_timeout(self, _: MagicMock, __: MagicMock) -> None:
        assert network_utils.wait_for_server_offline("localhost", 80, timeout_sec=0.3) is False


class TestIPAddressUtilities:
    @patch("netifaces.interfaces", return_value=["eth0", "wlan0"])
    @patch("netifaces.ifaddresses")
    def test_find_ip_addresses_matching_regex(self, mock_ifaddresses: MagicMock, _: MagicMock) -> None:
        mock_ifaddresses.side_effect = lambda iface: {
            socket.AF_INET: [{"addr": "192.168.1.101"}, {"addr": "10.0.0.5"}]
        }
        ips: list[str] = network_utils.find_ip_addresses(r"192\.168\.1\.\d+")
        assert ips == ["192.168.1.101"]

    @patch("netifaces.interfaces", return_value=["eth0"])
    @patch("netifaces.ifaddresses", return_value={socket.AF_INET: [{"addr": None}]})
    def test_find_ip_addresses_none_addr(self, _: MagicMock, __: MagicMock) -> None:
        assert not network_utils.find_ip_addresses(r".*")


class TestWirelessBand:
    @patch("platform.system", return_value=network_utils.SupportedPlatforms.MACOS)
    @patch.object(Path, "exists", return_value=True)
    @patch("subprocess.check_output")
    def test_24ghz(self, mock_subproc: MagicMock, _: MagicMock, __: MagicMock) -> None:
        mock_subproc.return_value = b"Current Network Information: ... PHY Mode ... Channel: 6"
        assert network_utils.get_wireless_band() == network_utils.WirelessBand.BAND_2_4_GHZ

    @patch("platform.system", return_value=network_utils.SupportedPlatforms.MACOS)
    @patch.object(Path, "exists", return_value=True)
    @patch("subprocess.check_output")
    def test_5ghz(self, mock_subproc: MagicMock, _: MagicMock, __: MagicMock) -> None:
        mock_subproc.return_value = b"Current Network Information: ... PHY Mode ... Channel: 44"
        assert network_utils.get_wireless_band() == network_utils.WirelessBand.BAND_5_GHZ

    @patch("platform.system", return_value=network_utils.SupportedPlatforms.MACOS)
    @patch.object(Path, "exists", return_value=True)
    @patch("subprocess.check_output", return_value=b"no channel info")
    def test_unknown(self, _: MagicMock, __: MagicMock, ___: MagicMock) -> None:
        assert network_utils.get_wireless_band() == network_utils.WirelessBand.BAND_UNKNOWN

    @patch("platform.system", return_value=network_utils.SupportedPlatforms.MACOS)
    @patch.object(Path, "exists", return_value=False)
    def test_file_missing(self, _: MagicMock, __: MagicMock) -> None:
        result: str = network_utils.get_wireless_band()
        assert result.startswith("Error: required file not found")

    @patch("platform.system", return_value="OtherOS")
    def test_unsupported(self, _: MagicMock) -> None:
        assert network_utils.get_wireless_band() == network_utils.WirelessBand.BAND_UNKNOWN


class TestScanForSSID:
    @patch("platform.system", return_value=network_utils.SupportedPlatforms.MACOS)
    @patch.object(Path, "exists", return_value=True)
    @patch("subprocess.check_output")
    def test_found(self, mock_subproc: MagicMock, _: MagicMock, __: MagicMock) -> None:
        mock_subproc.return_value = b"\n    TestSSID:\n    PHY Mode:"
        assert network_utils.scan_for_ssid("TestSSID", timeout_sec=0.1) is True

    @patch("platform.system", return_value=network_utils.SupportedPlatforms.MACOS)
    @patch.object(Path, "exists", return_value=True)
    @patch("subprocess.check_output", return_value=b"\n    OtherSSID:\n    PHY Mode:")
    def test_not_found_invert_true(self, _: MagicMock, __: MagicMock, ___: MagicMock) -> None:
        assert network_utils.scan_for_ssid("MissingSSID", timeout_sec=0.1, invert=True) is True

    @patch("platform.system", return_value=network_utils.SupportedPlatforms.MACOS)
    @patch.object(Path, "exists", return_value=True)
    @patch("subprocess.check_output", return_value=b"\n    OtherSSID:\n    PHY Mode:")
    def test_not_found_invert_false(self, _: MagicMock, __: MagicMock, ___: MagicMock) -> None:
        assert network_utils.scan_for_ssid("MissingSSID", timeout_sec=0.1, invert=False) is False

    @patch("platform.system", return_value="OtherOS")
    def test_unsupported(self, _: MagicMock) -> None:
        with pytest.raises(EnvironmentError):
            network_utils.scan_for_ssid("AnySSID")

    @patch("platform.system", return_value=network_utils.SupportedPlatforms.MACOS)
    @patch.object(Path, "exists", return_value=False)
    def test_file_missing(self, _: MagicMock, __: MagicMock) -> None:
        with pytest.raises(EnvironmentError):
            network_utils.scan_for_ssid("AnySSID")
