from datetime import datetime
from pathlib import Path

import pytest

from src.handlers.screenshot_handler import ScreenshotHandler


@pytest.fixture
def handler():
    return ScreenshotHandler()


class TestScreenshotHandlerConfig:
    def test_supported_extensions_include_common_screenshot_types(self, handler):
        exts = handler.supported_extensions()
        assert set(exts) >= {"png", "jpg", "jpeg"}

    def test_priority_is_fast_native(self, handler):
        assert handler.priority() == 10


class TestScreenshotDateExtraction:
    @pytest.mark.parametrize(
        "filename, expected_date",
        [
            # standard screenshot filenames
            ("Screenshot_20240615-143022.png", datetime(2024, 6, 15, 14, 30, 22)),
            ("Screenshot_20200315-091500.jpg", datetime(2020, 3, 15, 9, 15, 0)),
            ("Screenshot_20230423-183045.jpeg", datetime(2023, 4, 23, 18, 30, 45)),
            # midnight
            ("Screenshot_20190101-000000.png", datetime(2019, 1, 1, 0, 0, 0)),
            # end of day
            ("Screenshot_20201231-235959.png", datetime(2020, 12, 31, 23, 59, 59)),
            # case variations
            ("screenshot_20240615-143022.png", datetime(2024, 6, 15, 14, 30, 22)),
            ("SCREENSHOT_20240615-143022.png", datetime(2024, 6, 15, 14, 30, 22)),
            # with suffix (no end anchor)
            ("Screenshot_20240615-143022_Chrome.png", datetime(2024, 6, 15, 14, 30, 22)),
            ("Screenshot_20240615-143022 (2).png", datetime(2024, 6, 15, 14, 30, 22)),
        ],
        ids=lambda v: v if isinstance(v, str) else "",
    )
    def test_extracts_date_from_screenshot_filename(self, handler, filename, expected_date):
        result = handler.extract_metadata(Path(filename))
        assert result["date"] == expected_date

    def test_result_contains_only_date_key(self, handler):
        result = handler.extract_metadata(Path("Screenshot_20240615-143022.png"))
        assert list(result.keys()) == ["date"]


class TestScreenshotRejection:
    @pytest.mark.parametrize(
        "filename",
        [
            # not a screenshot name at all
            "holiday_photo.jpg",
            "photo_2023.png",
            # missing Screenshot prefix
            "20240615-143022.png",
            "Screen_20240615-143022.png",
            # wrong prefix
            "Screencap_20240615-143022.png",
            "Screen_Shot_20240615-143022.png",  # extra underscore
            # invalid dates
            "Screenshot_20241301-143022.png",  # month 13
            "Screenshot_20240631-143022.png",  # june 31
            "Screenshot_20240000-143022.png",  # month 0
            # invalid times
            "Screenshot_20240615-250000.png",  # hour 25
            "Screenshot_20240615-146000.png",  # minute 60
            "Screenshot_20240615-143060.png",  # second 60
            # wrong separators
            "Screenshot-20240615-143022.png",
            "Screenshot_2024-06-15_14-30-22.png",
            "Screenshot_20240615_143022.png",
            # truncated
            "Screenshot_2024061-143022.png",
            "Screenshot_20240615-14302.png",
        ],
        ids=lambda v: v,
    )
    def test_non_screenshot_or_invalid_returns_empty(self, handler, filename):
        result = handler.extract_metadata(Path(filename))
        assert result == {}

    def test_file_need_not_exist(self, handler):
        path = Path("/nonexistent/dir/Screenshot_20220101-120000.png")
        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2022, 1, 1, 12, 0, 0)


class TestScreenshotEdgeCases:
    def test_feb_29_leap_year_valid(self, handler):
        result = handler.extract_metadata(Path("Screenshot_20200229-120000.png"))
        assert result["date"] == datetime(2020, 2, 29, 12, 0, 0)

    def test_feb_29_non_leap_year_rejected(self, handler):
        result = handler.extract_metadata(Path("Screenshot_20210229-120000.png"))
        assert result == {}

    def test_allows_suffix_after_timestamp(self, handler):
        # Screenshot handler has no end anchor, allowing suffixes
        result = handler.extract_metadata(Path("Screenshot_20240615-143022_app.png"))
        assert result["date"] == datetime(2024, 6, 15, 14, 30, 22)
