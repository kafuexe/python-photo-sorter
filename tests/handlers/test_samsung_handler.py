from datetime import datetime
from pathlib import Path

import pytest

from src.handlers.samsung_handler import SamsungHandler


@pytest.fixture
def handler():
    return SamsungHandler()


class TestSamsungHandlerConfig:
    def test_supported_extensions_include_common_samsung_types(self, handler):
        exts = handler.supported_extensions()
        assert set(exts) >= {"jpg", "jpeg", "mp4"}

    def test_priority_is_fast_native(self, handler):
        assert handler.priority() == 10


class TestSamsungDateExtraction:
    @pytest.mark.parametrize(
        "filename, expected_date",
        [
            # standard image filenames
            ("20240615_143022.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("20200315_091500.jpeg", datetime(2020, 3, 15, 9, 15, 0)),
            # standard video filenames
            ("20230423_183045.mp4", datetime(2023, 4, 23, 18, 30, 45)),
            # midnight
            ("20190101_000000.jpg", datetime(2019, 1, 1, 0, 0, 0)),
            # end of day
            ("20201231_235959.mp4", datetime(2020, 12, 31, 23, 59, 59)),
        ],
        ids=lambda v: v if isinstance(v, str) else "",
    )
    def test_extracts_date_from_samsung_filename(self, handler, filename, expected_date):
        result = handler.extract_metadata(Path(filename))
        assert result["date"] == expected_date

    def test_result_contains_only_date_key(self, handler):
        result = handler.extract_metadata(Path("20240615_143022.jpg"))
        assert list(result.keys()) == ["date"]


class TestSamsungRejection:
    @pytest.mark.parametrize(
        "filename",
        [
            # not a samsung name at all
            "holiday_photo.jpg",
            "screenshot_2023.png",
            # prefix before date
            "IMG_20240615_143022.jpg",
            "PXL_20240615_143022.jpg",
            # extra suffix after timestamp
            "20240615_143022_edit.jpg",
            "20240615_143022_1.jpg",
            # invalid dates
            "20241301_143022.jpg",  # month 13
            "20240631_143022.jpg",  # june 31
            "20240000_143022.jpg",  # month 0
            # invalid times
            "20240615_250000.jpg",  # hour 25
            "20240615_146000.jpg",  # minute 60
            "20240615_143060.jpg",  # second 60
            # wrong separators
            "20240615-143022.jpg",
            "2024-06-15_14-30-22.jpg",
            # truncated
            "2024061_143022.jpg",
            "20240615_14302.jpg",
        ],
        ids=lambda v: v,
    )
    def test_non_samsung_or_invalid_returns_empty(self, handler, filename):
        result = handler.extract_metadata(Path(filename))
        assert result == {}

    def test_file_need_not_exist(self, handler):
        path = Path("/nonexistent/dir/20220101_120000.mp4")
        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2022, 1, 1, 12, 0, 0)


class TestSamsungEdgeCases:
    def test_feb_29_leap_year_valid(self, handler):
        result = handler.extract_metadata(Path("20200229_120000.jpg"))
        assert result["date"] == datetime(2020, 2, 29, 12, 0, 0)

    def test_feb_29_non_leap_year_rejected(self, handler):
        result = handler.extract_metadata(Path("20210229_120000.jpg"))
        assert result == {}

    def test_strict_end_anchor_rejects_suffix(self, handler):
        # Samsung handler uses $ anchor, so any suffix should be rejected
        result = handler.extract_metadata(Path("20240615_143022_extra.jpg"))
        assert result == {}
