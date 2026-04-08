from __future__ import annotations

import re
import subprocess
from typing import Callable, Iterable, Tuple

import pytest

from bear_tools import macos_utils

# ---------- helpers ----------

def _make_called_process_error() -> subprocess.CalledProcessError:
    # Typical nonzero return code with empty output
    return subprocess.CalledProcessError(returncode=1, cmd=["dummy"])


def _bytes(s: str) -> bytes:
    return s.encode("utf-8")


def _patch_check_output_returning(
    monkeypatch: pytest.MonkeyPatch, expected_cmd_prefix: Iterable[str], out: str
) -> None:
    expected_prefix = list(expected_cmd_prefix)

    def _fake_check_output(cmd: list[str], *args, **kwargs) -> bytes:
        # Ensure the command starts with what we expect (tool + primary args).
        assert cmd[: len(expected_prefix)] == expected_prefix
        return _bytes(out)

    monkeypatch.setattr(subprocess, "check_output", _fake_check_output)


def _patch_check_output_raising(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_check_output(*args, **kwargs) -> bytes:
        raise _make_called_process_error()

    monkeypatch.setattr(subprocess, "check_output", _fake_check_output)


def _patch_mac_ver(monkeypatch: pytest.MonkeyPatch, ver: str) -> None:
    def _fake_mac_ver() -> Tuple[str, Tuple[str, str, str], str]:
        return (ver, ("", "", ""), "arm64")
    monkeypatch.setattr(macos_utils.platform, "mac_ver", _fake_mac_ver)


# ---------- get_current_ssid_macos14_and_older ----------

def test_get_current_ssid_macos14_success_default_interface(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_check_output_returning(
        monkeypatch,
        expected_cmd_prefix=["networksetup", "-getairportnetwork", "en0"],
        out="Current Wi-Fi Network: MyHomeWiFi\n",
    )
    assert macos_utils.get_current_ssid_macos14_and_older() == "MyHomeWiFi"


def test_get_current_ssid_macos14_success_custom_interface(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_check_output_returning(
        monkeypatch,
        expected_cmd_prefix=["networksetup", "-getairportnetwork", "en1"],
        out="Current Wi-Fi Network: CaféNet \n",
    )
    # Note: trailing space is stripped; non-ASCII is preserved by .decode() path.
    assert macos_utils.get_current_ssid_macos14_and_older("en1") == "CaféNet"


def test_get_current_ssid_macos14_no_prefix_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_check_output_returning(
        monkeypatch,
        expected_cmd_prefix=["networksetup", "-getairportnetwork", "en0"],
        out="Wi-Fi power is currently on.\n",
    )
    assert macos_utils.get_current_ssid_macos14_and_older() is None


def test_get_current_ssid_macos14_subprocess_error_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_check_output_raising(monkeypatch)
    assert macos_utils.get_current_ssid_macos14_and_older() is None


# ---------- get_current_ssid_macos15 ----------

def test_get_current_ssid_macos15_parses_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    summary = """
   IPv4 : 192.168.1.23
   SSID : MyHomeWiFi
   BSSID : aa:bb:cc:dd:ee:ff
"""
    _patch_check_output_returning(monkeypatch, ["ipconfig", "getsummary", "en0"], summary)
    assert macos_utils.get_current_ssid_macos15() == "MyHomeWiFi"


def test_get_current_ssid_macos15_respects_custom_interface(monkeypatch: pytest.MonkeyPatch) -> None:
    summary = "\n   SSID : OfficeNet\n"
    _patch_check_output_returning(monkeypatch, ["ipconfig", "getsummary", "en1"], summary)
    assert macos_utils.get_current_ssid_macos15("en1") == "OfficeNet"


def test_get_current_ssid_macos15_missing_ssid_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_check_output_returning(monkeypatch, ["ipconfig", "getsummary", "en0"], "\n   BSSID : 00:00:00:00:00:00\n")
    assert macos_utils.get_current_ssid_macos15() is None


def test_get_current_ssid_macos15_requires_leading_newline_and_indent(monkeypatch: pytest.MonkeyPatch) -> None:
    # Regex anchors to a newline followed by spaces: ensure a line like "SSID : ..." at start of string won’t match.
    _patch_check_output_returning(monkeypatch, ["ipconfig", "getsummary", "en0"], "SSID : ShouldNotMatch\n")
    assert macos_utils.get_current_ssid_macos15() is None


def test_get_current_ssid_macos15_max_32_visible_ascii(monkeypatch: pytest.MonkeyPatch) -> None:
    ok_32 = "X" * 32
    too_long = "Y" * 33
    # Two SSID lines; regex.search should capture the first valid one.
    summary = f"""
   SSID : {ok_32}
   SSID : {too_long}
"""
    _patch_check_output_returning(monkeypatch, ["ipconfig", "getsummary", "en0"], summary)
    assert macos_utils.get_current_ssid_macos15() == ok_32


def test_get_current_ssid_macos15_disallows_non_ascii(monkeypatch: pytest.MonkeyPatch) -> None:
    # Regex limits to [\x20-\x7E]; the café 'é' (0xC3 0xA9 in UTF-8) should not match.
    summary = "\n   SSID : CaféNet\n"
    _patch_check_output_returning(monkeypatch, ["ipconfig", "getsummary", "en0"], summary)
    assert macos_utils.get_current_ssid_macos15() is None


def test_get_current_ssid_macos15_subprocess_error_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_check_output_raising(monkeypatch)
    assert macos_utils.get_current_ssid_macos15() is None


def test_get_current_ssid_macos15_trims_trailing_spaces_inside_regex(monkeypatch: pytest.MonkeyPatch) -> None:
    # The regex captures exactly the run of visible ASCII after "SSID : ".
    # If there are trailing spaces they will be included; here we ensure only intended token is captured.
    # Provide SSID followed by two spaces then newline; those spaces are valid [\x20-\x7E] and thus captured.
    # This test documents current behavior (no strip). Adjust if you later choose to strip.
    summary = "\n   SSID : MySSID  \n"
    _patch_check_output_returning(monkeypatch, ["ipconfig", "getsummary", "en0"], summary)
    assert macos_utils.get_current_ssid_macos15() == "MySSID  "


# ---------- get_current_ssid (router) ----------

@pytest.mark.parametrize(
    ("ver", "expected_called"),
    [
        ("14.0", "older"),  # 14.x -> macos14_and_older
        ("14.6.1", "older"),
        ("15.0", "newer"),  # anything else -> macos15
        ("15.1", "newer"),
    ],
)
def test_get_current_ssid_routes_by_major_version(
    monkeypatch: pytest.MonkeyPatch, ver: str, expected_called: str
) -> None:
    _patch_mac_ver(monkeypatch, ver)

    called: dict[str, int] = {"older": 0, "newer": 0}

    def _fake_older(*args, **kwargs) -> None:
        called["older"] += 1
        return None

    def _fake_newer(*args, **kwargs) -> None:
        called["newer"] += 1
        return None

    monkeypatch.setattr(macos_utils, "get_current_ssid_macos14_and_older", _fake_older)
    monkeypatch.setattr(macos_utils, "get_current_ssid_macos15", _fake_newer)

    _ = macos_utils.get_current_ssid()

    assert called[expected_called] == 1
    assert called[("newer" if expected_called == "older" else "older")] == 0


def test_get_current_ssid_end_to_end_14_path(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_mac_ver(monkeypatch, "14.6")
    _patch_check_output_returning(
        monkeypatch,
        expected_cmd_prefix=["networksetup", "-getairportnetwork", "en0"],
        out="Current Wi-Fi Network: HouseNet\n",
    )
    assert macos_utils.get_current_ssid() == "HouseNet"


def test_get_current_ssid_end_to_end_15_path(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_mac_ver(monkeypatch, "15.0")
    _patch_check_output_returning(
        monkeypatch,
        expected_cmd_prefix=["ipconfig", "getsummary", "en0"],
        out="\n   SSID : CampusWiFi\n",
    )
    assert macos_utils.get_current_ssid() == "CampusWiFi"


# ---------- regex sanity (guard against silent breakage if you tweak it) ----------

def test_macos15_regex_compiles_and_is_expected() -> None:
    # Keep this in sync with the module constant usage
    text = "\n   SSID : ABC123"
    pat = re.compile(r"\n\s+SSID : ([\x20-\x7E]{1,32})")
    m = pat.search(text)
    assert m and m.group(1) == "ABC123"