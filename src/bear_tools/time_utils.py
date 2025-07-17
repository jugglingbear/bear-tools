"""
Useful time-related functions
"""

import re
import subprocess
from datetime import datetime

import pytz

# UTC offset constants based on https://en.wikipedia.org/wiki/List_of_UTC_offsets
MIN_UTC_OFFSET_MINUTES = -12 * 60  # UTC-12
MAX_UTC_OFFSET_MINUTES = 14 * 60   # UTC+14


def get_local_timestamp_description(dt: datetime, utc_offset_minutes: int, dst: bool) -> str:
    """
    Get an "aware" (i.e. contains timezone info) date/time/timezone/dst string

    :param dt: A naive datetime object
    :param utc_offset_minutes: UTC offset in minutes
    :param dst: True if Daylight Savings Time is active; False otherwise
    :return: A string of the form YYYY-mm-dd HH:MM:SS(+/-)XXYY where XX is UTC offset hours and YY is UTC offset minutes
    """

    base_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
    dst_status = "ON" if dst else "OFF"

    # Valid UTC offset
    if MIN_UTC_OFFSET_MINUTES <= utc_offset_minutes <= MAX_UTC_OFFSET_MINUTES:
        # Use divmod for cleaner hour/minute calculation
        offset_hours, offset_minutes = divmod(abs(utc_offset_minutes), 60)
        sign = '+' if utc_offset_minutes >= 0 else '-'
        utc_offset_str = f'(UTC{sign}{offset_hours:02}:{offset_minutes:02})'
        return f'{base_timestamp} {utc_offset_str} (DST: {dst_status})'

    # Invalid UTC offset - fallback format
    return f'{base_timestamp} (UTC Offset minutes: {utc_offset_minutes}) (DST: {dst_status})'


def get_local_timestamp_filename(dt: datetime, utc_offset_minutes: int, dst: bool) -> str:
    """
    Get an "aware" (i.e. contains timezone info) date/time/timezone/dst filename

    :param dt: A naive datetime object
    :param utc_offset_minutes: UTC offset in minutes
    :param dst: True if Daylight Savings Time is active; False otherwise
    :return: A string of the form YYYYmmdd_HHMMSS_(neg)XXYY_Z where XX is UTC offset hours, YY is min, Z is "DST-ON/OFF"
    """

    # Valid UTC offset
    if MIN_UTC_OFFSET_MINUTES <= utc_offset_minutes <= MAX_UTC_OFFSET_MINUTES:
        base_timestamp = dt.strftime('%Y%m%d_%H%M%S')

        # Use divmod for cleaner hour/minute calculation
        offset_hours, offset_minutes = divmod(abs(utc_offset_minutes), 60)
        sign_prefix = '' if utc_offset_minutes >= 0 else 'neg'
        utc_offset_str = f'{sign_prefix}{offset_hours:02}{offset_minutes:02}'
        dst_status = f'DST-{"ON" if dst else "OFF"}'

        return f'{base_timestamp}_{utc_offset_str}_{dst_status}'

    raise ValueError(
        'Invalid utc_offset_minutes. '
        f'Should be {MIN_UTC_OFFSET_MINUTES} <= {utc_offset_minutes} <= {MAX_UTC_OFFSET_MINUTES}'
    )


def get_local_time(timezone: str) -> datetime:
    """
    Get local time based on timezone string

    :param timezone: A timezone string as defined by site-packages/pytz/__init__.py
    :return: An "aware" datetime object (i.e. contains timezone data)
    """

    utc_time = datetime.now(tz=pytz.timezone('UTC'))
    local_timezone = pytz.timezone(timezone)
    return utc_time.astimezone(tz=local_timezone)


def get_local_utc_offset_minutes() -> int | None:
    """
    Get the local UTC offset in minutes
    """

    try:
        raw_output = subprocess.check_output(['date', '+%z'], text=True)
    except subprocess.CalledProcessError:
        return None

    matches = re.findall(r'([+-])([0-9]{2})([0-9]{2})', raw_output)
    if not matches:
        return None

    sign_str, hours_str, minutes_str = matches[0]
    sign = -1 if sign_str == '-' else 1
    hours = int(hours_str)
    minutes = int(minutes_str)

    return sign * (hours * 60 + minutes)


def get_logging_timestamp() -> str:
    """
    Get the current time in the form: "YYYY-mm-dd HH:MM:SS.xxx"

    Note: xxx is milliseconds (truncated from microseconds)
    """

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def get_filename_timestamp(include_microseconds: bool = False) -> str:
    """
    Get the current time in the form: "YYYYmmdd-HHMMSS" or "YYYYmmdd-HHMMSS-xxx"

    :param include_microseconds: If True, include milliseconds in the timestamp; otherwise don't
    """

    now = datetime.now()
    if include_microseconds:
        return now.strftime("%Y%m%d-%H%M%S-%f")[:-3]  # Truncate to milliseconds
    else:
        return now.strftime("%Y%m%d-%H%M%S")


def get_utc_offsets() -> list[int]:
    """
    Get a list of UTC offsets in minutes from the pytz package.

    As of pytz==2022.1, there are some differences between existing UTC offsets in the package vs offsets
    listed in wikipedia. For now, it is regarded as good enough.

    As of 2023-10-11, there are 38 UTC offsets

    Source:
        https://en.wikipedia.org/wiki/List_of_UTC_offsets
        2023-10-11: As of today, there are 38 UTC offsets
    """

    now = datetime.now()
    utc_offsets = {
        int(pytz.timezone(timezone_name).utcoffset(now).total_seconds() / 60)
        for timezone_name in pytz.all_timezones_set
    }

    return sorted(utc_offsets)


def is_datetime_naive(timestamp: datetime) -> bool:
    """
    Determine if datetime object is naive (does not contain timezone info) or aware (contains timezone info)

    Source:
        https://docs.python.org/3.9/library/datetime.html#determining-if-an-object-is-aware-or-naive

    :param timestamp: A datetime object
    :return: True if object is naive; otherwise False
    """

    return timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None
