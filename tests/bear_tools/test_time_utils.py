# flake8: noqa: E501
# pylint: disable=C0301,C0116

"""
Unit tests for time_utils.py
"""

import subprocess
from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest
import pytz

from bear_tools import time_utils as tu


def test_get_local_timestamp_description_valid_offsets() -> None:
    dt: datetime = datetime(2024, 5, 17, 15, 30, 45)
    result_positive: str = tu.get_local_timestamp_description(dt, 330, True)
    assert result_positive.startswith("2024-05-17 15:30:45")
    assert "(UTC+05:30)" in result_positive
    assert "(DST: ON)" in result_positive
    result_negative: str = tu.get_local_timestamp_description(dt, -480, False)
    assert "(UTC-08:00)" in result_negative
    assert "(DST: OFF)" in result_negative


def test_get_local_timestamp_description_invalid_offsets() -> None:
    dt: datetime = datetime(2024, 5, 17, 15, 30, 45)
    result: str = tu.get_local_timestamp_description(dt, 10000, False)
    assert "(UTC Offset minutes: 10000)" in result
    assert "(DST: OFF)" in result


def test_get_local_timestamp_filename_valid_offsets() -> None:
    dt: datetime = datetime(2024, 5, 17, 15, 30, 45)
    result_positive: str = tu.get_local_timestamp_filename(dt, 120, True)
    assert result_positive.startswith("20240517_153045")
    assert "_0200_" in result_positive
    assert result_positive.endswith("DST-ON")
    result_negative: str = tu.get_local_timestamp_filename(dt, -345, False)
    assert "_neg0545_" in result_negative
    assert result_negative.endswith("DST-OFF")


def test_get_local_timestamp_filename_invalid_offsets_raises() -> None:
    dt: datetime = datetime(2024, 5, 17, 15, 30, 45)
    with pytest.raises(ValueError):
        tu.get_local_timestamp_filename(dt, 10000, True)


def test_get_local_time_returns_aware() -> None:
    local_dt: datetime = tu.get_local_time("Asia/Kolkata")
    assert isinstance(local_dt, datetime)
    assert local_dt.tzinfo is not None
    assert "India" in str(local_dt.tzinfo) or "Asia" in str(local_dt.tzinfo)


@patch("subprocess.check_output", return_value="+0530")
def test_get_local_utc_offset_minutes_valid(_mock_subprocess: Any) -> None:
    offset: int | None = tu.get_local_utc_offset_minutes()
    assert offset == 330


@patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "date"))
def test_get_local_utc_offset_minutes_called_process_error(_mock_subprocess: Any) -> None:
    offset: int | None = tu.get_local_utc_offset_minutes()
    assert offset is None


@patch("subprocess.check_output", return_value="invalid")
def test_get_local_utc_offset_minutes_invalid_format(_mock_subprocess: Any) -> None:
    offset: int | None = tu.get_local_utc_offset_minutes()
    assert offset is None


def test_get_logging_timestamp_format() -> None:
    ts: str = tu.get_logging_timestamp()
    assert len(ts) == 23
    assert ts[4] == "-"
    assert ts[7] == "-"
    assert ts[10] == " "
    assert "." in ts


def test_get_filename_timestamp_formats() -> None:
    ts_no_micro: str = tu.get_filename_timestamp()
    assert len(ts_no_micro) == 15
    assert ts_no_micro[8] == "-"
    ts_with_micro: str = tu.get_filename_timestamp(include_microseconds=True)
    assert len(ts_with_micro) == 19
    assert ts_with_micro[8] == "-"
    assert ts_with_micro.count("-") == 2


def test_get_utc_offsets_returns_valid_range() -> None:
    offsets: list[int] = tu.get_utc_offsets()
    assert isinstance(offsets, list)
    assert all(isinstance(x, int) for x in offsets)
    assert tu.MIN_UTC_OFFSET_MINUTES <= min(offsets)
    assert max(offsets) <= tu.MAX_UTC_OFFSET_MINUTES
    assert len(offsets) >= 30  # pytz currently has ~38


def test_is_datetime_naive_true_false() -> None:
    naive_dt: datetime = datetime(2024, 5, 17, 12, 0, 0)
    aware_dt: datetime = datetime.now(tz=pytz.UTC)
    assert tu.is_datetime_naive(naive_dt) is True
    assert tu.is_datetime_naive(aware_dt) is False
