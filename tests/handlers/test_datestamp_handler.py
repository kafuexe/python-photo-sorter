from datetime import datetime
from pathlib import Path

import pytest

from src.handlers.datestamp_handler import DatestampHandler


@pytest.fixture
def handler():
    return DatestampHandler()


class TestDatestampHandlerConfig:
    def test_supported_extensions_include_common_media_types(self, handler):
        exts = handler.supported_extensions()
        assert set(exts) >= {"jpg", "jpeg", "png", "mp4"}

    def test_priority_is_fallback(self, handler):
        # Priority 15 is higher number = lower priority = fallback
        assert handler.priority() == 15


class TestDatestampDateExtraction:
    @pytest.mark.parametrize(
        "filename, expected_date",
        [
            # space separator between date and time
            ("2024-06-15 14.30.22.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("2020-03-15 09.15.00.jpeg", datetime(2020, 3, 15, 9, 15, 0)),
            ("2023-04-23 18.30.45.mp4", datetime(2023, 4, 23, 18, 30, 45)),
            # underscore separator between date and time
            ("2024-06-15_14.30.22.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("2020-03-15_09.15.00.png", datetime(2020, 3, 15, 9, 15, 0)),
            # midnight
            ("2019-01-01 00.00.00.jpg", datetime(2019, 1, 1, 0, 0, 0)),
            # end of day
            ("2020-12-31 23.59.59.mp4", datetime(2020, 12, 31, 23, 59, 59)),
            # with suffix (no end anchor)
            ("2024-06-15 14.30.22 holiday.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("2024-06-15_14.30.22_edited.png", datetime(2024, 6, 15, 14, 30, 22)),
        ],
        ids=lambda v: v if isinstance(v, str) else "",
    )
    def test_extracts_date_from_datestamp_filename(self, handler, filename, expected_date):
        result = handler.extract_metadata(Path(filename))
        assert result["date"] == expected_date

    def test_result_contains_only_date_key(self, handler):
        result = handler.extract_metadata(Path("2024-06-15 14.30.22.jpg"))
        assert list(result.keys()) == ["date"]


class TestDatestampRejection:
    @pytest.mark.parametrize(
        "filename",
        [
            # not a datestamp name at all
            "holiday_photo.jpg",
            "screenshot_2023.png",
            # wrong date format
            "20240615 14.30.22.jpg",  # no dashes in date
            "2024/06/15 14.30.22.jpg",  # slashes
            # wrong time format
            "2024-06-15 14:30:22.jpg",  # colons
            "2024-06-15 143022.jpg",  # no separators
            "2024-06-15 14-30-22.jpg",  # dashes in time
            # wrong separator between date and time
            "2024-06-15-14.30.22.jpg",  # dash
            "2024-06-15T14.30.22.jpg",  # T
            # invalid dates
            "2024-13-01 14.30.22.jpg",  # month 13
            "2024-06-31 14.30.22.jpg",  # june 31
            "2024-00-01 14.30.22.jpg",  # month 0
            # invalid times
            "2024-06-15 25.00.00.jpg",  # hour 25
            "2024-06-15 14.60.00.jpg",  # minute 60
            "2024-06-15 14.30.60.jpg",  # second 60
            # truncated
            "2024-06-1 14.30.22.jpg",
            "2024-06-15 14.30.2.jpg",
        ],
        ids=lambda v: v,
    )
    def test_non_datestamp_or_invalid_returns_empty(self, handler, filename):
        result = handler.extract_metadata(Path(filename))
        assert result == {}

    def test_file_need_not_exist(self, handler):
        path = Path("/nonexistent/dir/2022-01-01 12.00.00.mp4")
        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2022, 1, 1, 12, 0, 0)


class TestDatestampEdgeCases:
    def test_feb_29_leap_year_valid(self, handler):
        result = handler.extract_metadata(Path("2020-02-29 12.00.00.jpg"))
        assert result["date"] == datetime(2020, 2, 29, 12, 0, 0)

    def test_feb_29_non_leap_year_rejected(self, handler):
        result = handler.extract_metadata(Path("2021-02-29 12.00.00.jpg"))
        assert result == {}

    def test_allows_suffix_after_timestamp(self, handler):
        # Datestamp handler has no end anchor, allowing suffixes
        result = handler.extract_metadata(Path("2024-06-15 14.30.22 beach trip.jpg"))
        assert result["date"] == datetime(2024, 6, 15, 14, 30, 22)

    def test_is_lower_priority_than_specific_handlers(self, handler):
        # Datestamp handler is a fallback at priority 15
        from src.handlers.samsung_handler import SamsungHandler
        from src.handlers.pixel_handler import PixelHandler

        assert handler.priority() > SamsungHandler().priority()
        assert handler.priority() > PixelHandler().priority()
