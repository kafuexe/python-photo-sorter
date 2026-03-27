from datetime import datetime
from pathlib import Path

import pytest

from src.handlers.pixel_handler import PixelHandler


@pytest.fixture
def handler():
    return PixelHandler()


class TestPixelHandlerConfig:
    def test_supported_extensions_include_common_pixel_types(self, handler):
        exts = handler.supported_extensions()
        assert set(exts) >= {"jpg", "jpeg", "mp4"}

    def test_priority_is_fast_native(self, handler):
        assert handler.priority() == 10


class TestPixelDateExtraction:
    @pytest.mark.parametrize(
        "filename, expected_date",
        [
            # standard image filenames
            ("PXL_20240615_143022.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("PXL_20200315_091500.jpeg", datetime(2020, 3, 15, 9, 15, 0)),
            # standard video filenames
            ("PXL_20230423_183045.mp4", datetime(2023, 4, 23, 18, 30, 45)),
            # midnight
            ("PXL_20190101_000000.jpg", datetime(2019, 1, 1, 0, 0, 0)),
            # end of day
            ("PXL_20201231_235959.mp4", datetime(2020, 12, 31, 23, 59, 59)),
            # case variations
            ("pxl_20240615_143022.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("Pxl_20240615_143022.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            # with suffix (no end anchor)
            ("PXL_20240615_143022_TS.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("PXL_20240615_143022.NIGHT.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("PXL_20240615_143022_PORTRAIT.jpg", datetime(2024, 6, 15, 14, 30, 22)),
        ],
        ids=lambda v: v if isinstance(v, str) else "",
    )
    def test_extracts_date_from_pixel_filename(self, handler, filename, expected_date):
        result = handler.extract_metadata(Path(filename))
        assert result["date"] == expected_date

    def test_result_contains_only_date_key(self, handler):
        result = handler.extract_metadata(Path("PXL_20240615_143022.jpg"))
        assert list(result.keys()) == ["date"]


class TestPixelRejection:
    @pytest.mark.parametrize(
        "filename",
        [
            # not a pixel name at all
            "holiday_photo.jpg",
            "screenshot_2023.png",
            # missing PXL prefix
            "20240615_143022.jpg",
            "IMG_20240615_143022.jpg",
            # wrong prefix
            "PIX_20240615_143022.jpg",
            "PIXEL_20240615_143022.jpg",
            # invalid dates
            "PXL_20241301_143022.jpg",  # month 13
            "PXL_20240631_143022.jpg",  # june 31
            "PXL_20240000_143022.jpg",  # month 0
            # invalid times
            "PXL_20240615_250000.jpg",  # hour 25
            "PXL_20240615_146000.jpg",  # minute 60
            "PXL_20240615_143060.jpg",  # second 60
            # wrong separators
            "PXL-20240615-143022.jpg",
            "PXL_2024-06-15_14-30-22.jpg",
            # truncated
            "PXL_2024061_143022.jpg",
            "PXL_20240615_14302.jpg",
        ],
        ids=lambda v: v,
    )
    def test_non_pixel_or_invalid_returns_empty(self, handler, filename):
        result = handler.extract_metadata(Path(filename))
        assert result == {}

    def test_file_need_not_exist(self, handler):
        path = Path("/nonexistent/dir/PXL_20220101_120000.mp4")
        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2022, 1, 1, 12, 0, 0)


class TestPixelEdgeCases:
    def test_feb_29_leap_year_valid(self, handler):
        result = handler.extract_metadata(Path("PXL_20200229_120000.jpg"))
        assert result["date"] == datetime(2020, 2, 29, 12, 0, 0)

    def test_feb_29_non_leap_year_rejected(self, handler):
        result = handler.extract_metadata(Path("PXL_20210229_120000.jpg"))
        assert result == {}

    def test_allows_suffix_after_timestamp(self, handler):
        # Pixel handler has no end anchor, allowing suffixes like _TS, .NIGHT, etc.
        result = handler.extract_metadata(Path("PXL_20240615_143022_edited.jpg"))
        assert result["date"] == datetime(2024, 6, 15, 14, 30, 22)
