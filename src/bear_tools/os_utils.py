import os
import subprocess
import sys
from enum import Enum
from pathlib import Path

from bear_tools import lumberjack

logger = lumberjack.Logger()


class Platform(Enum):
    """Supported platforms"""

    MACOS = 'darwin'


def is_pid_running(pid: int) -> bool:
    """
    Determine if a process is running

    :param pid: The process id
    :return: True if the process is running; False otherwise
    """

    try:
        os.kill(pid, 0)  # 0 -> noop signal for testing
    except OSError:
        return False
    return True


def play_media_with_vlc(path: Path, play_and_exit: bool = False) -> None:
    """
    Play a video using a locally-installed version of VLC

    Prerequisite: VLC must be installed!

    macOS: brew install vlc
    Linux: sudo apt update && sudo apt install vlc
    Windows: TODO

    :param path: Path of the media file to be played
    :param play_and_exit: If True, exit VLC automatically and close the file when it finishes playing
    """

    if sys.platform == Platform.MACOS.value:
        flags: str = '--play-and-exit' if play_and_exit else ''
        args: list[str] = ['vlc', flags, str(path)] if flags else ['vlc', str(path)]
        logger.info(f'Running command: "{args}"')
        try:
            subprocess.run(args, check=False)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f'Failed to play media file: "{path}". Error: "{error}"') from error

    # TODO: Add+test on Linux
    # TODO: Add+test on Windows


def popup_notification(title: str | None, subtitle: str | None, message: str) -> bool:
    """
    Display a popup notification in the OS, if possible

    :param title: The title of the OSD
    :param subtitle: The subtitle of the OSD
    :param message: The main text of the OSD
    :return: True if the popup was displayed; False otherwise
    """

    # Display a popup notification to the user that the test plan has finished running
    if sys.platform == Platform.MACOS.value:
        try:
            subprocess.check_call(
                f'terminal-notifier -title "{title}" -subtitle "{subtitle}" -message "{message}"',
                shell=True
            )
            return True
        except subprocess.CalledProcessError:
            logger.warning(
                'terminal-notifier not installed. '
                'No notification popups can be displayed when testing is complete. '
                'Use "brew install terminal-notifier" to install (if you want to). '
                'You may have to enable notifications in System Settings >> Notifications >> [your terminal name]'
            )
            return False
    return False


def say(message: str) -> None:
    """
    Announce something audibly

    :param message: Whatever the OS should say aloud
    """

    if sys.platform == Platform.MACOS.value:
        try:
            subprocess.check_call(f"/usr/bin/say '{message}'", shell=True)
        except subprocess.CalledProcessError:
            pass
        except FileNotFoundError:
            pass
