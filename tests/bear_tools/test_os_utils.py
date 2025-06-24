# pylint: disable=C0116

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from bear_tools.os_utils import Platform, is_pid_running, play_media_with_vlc, popup_notification, say


def test_is_pid_running_success() -> None:
    with patch("os.kill") as mock_kill:
        mock_kill.return_value = None
        assert is_pid_running(12345) is True
        mock_kill.assert_called_once_with(12345, 0)


def test_is_pid_running_failure() -> None:
    with patch("os.kill", side_effect=OSError):
        assert is_pid_running(12345) is False


@pytest.mark.parametrize("play_and_exit,expected_args", [
    (False, ['vlc', '/some/file.mp4']),
    (True, ['vlc', '--play-and-exit', '/some/file.mp4']),
])
def test_play_media_with_vlc_mac(play_and_exit: bool, expected_args: list[str]) -> None:
    with (
        patch("sys.platform", Platform.MACOS.value),
        patch("subprocess.run") as mock_run,
    ):
        path = Path("/some/file.mp4")
        play_media_with_vlc(path, play_and_exit=play_and_exit)
        mock_run.assert_called_once_with(expected_args, check=False)


def test_play_media_with_vlc_error() -> None:
    with (
        patch("sys.platform", Platform.MACOS.value),
        patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, 'vlc'))
    ):
        path = Path("/bad/file.mp4")
        with pytest.raises(RuntimeError, match='Failed to play media file'):
            play_media_with_vlc(path)


def test_popup_notification_success() -> None:
    with (
        patch("sys.platform", Platform.MACOS.value),
        patch("subprocess.check_call") as mock_call
    ):
        result = popup_notification("Title", "Subtitle", "Message")
        assert result is True
        expected_command = 'terminal-notifier -title "Title" -subtitle "Subtitle" -message "Message"'
        mock_call.assert_called_once_with(expected_command, shell=True)


def test_popup_notification_failure() -> None:
    with (
        patch("sys.platform", Platform.MACOS.value),
        patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, 'terminal-notifier'))
    ):
        result = popup_notification("Oops", "Error", "Broke")
        assert result is False


def test_popup_notification_non_macos() -> None:
    with patch("sys.platform", "linux"):
        assert popup_notification("Any", "Thing", "Ignored") is False


def test_say_success() -> None:
    with (
        patch("sys.platform", Platform.MACOS.value),
        patch("subprocess.check_call") as mock_call
    ):
        say("Hello")
        mock_call.assert_called_once_with("/usr/bin/say 'Hello'", shell=True)


def test_say_command_failure() -> None:
    with (
        patch("sys.platform", Platform.MACOS.value),
        patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, 'say'))
    ):
        say("Oops")  # Should silently ignore


def test_say_file_not_found() -> None:
    with (
        patch("sys.platform", Platform.MACOS.value),
        patch("subprocess.check_call", side_effect=FileNotFoundError)
    ):
        say("No file found")  # Should silently ignore
