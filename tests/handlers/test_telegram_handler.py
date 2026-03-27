from datetime import datetime
from pathlib import Path

import pytest

from src.handlers.telegram_handler import TelegramHandler


@pytest.fixture
def handler():
    return TelegramHandler()


class TestTelegramHandlerConfig:
    def test_supported_extensions_include_common_telegram_types(self, handler):
        exts = handler.supported_extensions()
        assert set(exts) >= {"jpg", "jpeg", "mp4"}

    def test_priority_is_fast_native(self, handler):
        assert handler.priority() == 10


class TestTelegramDateExtraction:
    @pytest.mark.parametrize(
        "filename, expected_date",
        [
            # photo filenames
            ("photo_2024-06-15_14-30-22.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("photo_2020-03-15_09-15-00.jpeg", datetime(2020, 3, 15, 9, 15, 0)),
            # video filenames
            ("video_2023-04-23_18-30-45.mp4", datetime(2023, 4, 23, 18, 30, 45)),
            # midnight
            ("photo_2019-01-01_00-00-00.jpg", datetime(2019, 1, 1, 0, 0, 0)),
            # end of day
            ("video_2020-12-31_23-59-59.mp4", datetime(2020, 12, 31, 23, 59, 59)),
            # case variations
            ("Photo_2024-06-15_14-30-22.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("VIDEO_2024-06-15_14-30-22.mp4", datetime(2024, 6, 15, 14, 30, 22)),
            ("PHOTO_2024-06-15_14-30-22.jpg", datetime(2024, 6, 15, 14, 30, 22)),
            # with suffix (no end anchor)
            ("photo_2024-06-15_14-30-22 (2).jpg", datetime(2024, 6, 15, 14, 30, 22)),
            ("video_2024-06-15_14-30-22_edit.mp4", datetime(2024, 6, 15, 14, 30, 22)),
        ],
        ids=lambda v: v if isinstance(v, str) else "",
    )
    def test_extracts_date_from_telegram_filename(self, handler, filename, expected_date):
        result = handler.extract_metadata(Path(filename))
        assert result["date"] == expected_date

    def test_result_contains_only_date_key(self, handler):
        result = handler.extract_metadata(Path("photo_2024-06-15_14-30-22.jpg"))
        assert list(result.keys()) == ["date"]


class TestTelegramRejection:
    @pytest.mark.parametrize(
        "filename",
        [
            # not a telegram name at all
            "holiday_photo.jpg",
            "screenshot_2023.png",
            # missing photo/video prefix
            "image_2024-06-15_14-30-22.jpg",
            "2024-06-15_14-30-22.jpg",
            # wrong prefix
            "pic_2024-06-15_14-30-22.jpg",
            "movie_2024-06-15_14-30-22.mp4",
            # invalid dates
            "photo_2024-13-01_14-30-22.jpg",  # month 13
            "photo_2024-06-31_14-30-22.jpg",  # june 31
            "photo_2024-00-01_14-30-22.jpg",  # month 0
            # invalid times
            "photo_2024-06-15_25-00-00.jpg",  # hour 25
            "photo_2024-06-15_14-60-00.jpg",  # minute 60
            "photo_2024-06-15_14-30-60.jpg",  # second 60
            # wrong separators
            "photo-2024-06-15-14-30-22.jpg",
            "photo_20240615_143022.jpg",
            # truncated
            "photo_2024-06-1_14-30-22.jpg",
            "photo_2024-06-15_14-30-2.jpg",
        ],
        ids=lambda v: v,
    )
    def test_non_telegram_or_invalid_returns_empty(self, handler, filename):
        result = handler.extract_metadata(Path(filename))
        assert result == {}

    def test_file_need_not_exist(self, handler):
        path = Path("/nonexistent/dir/photo_2022-01-01_12-00-00.mp4")
        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2022, 1, 1, 12, 0, 0)


class TestTelegramEdgeCases:
    def test_feb_29_leap_year_valid(self, handler):
        result = handler.extract_metadata(Path("photo_2020-02-29_12-00-00.jpg"))
        assert result["date"] == datetime(2020, 2, 29, 12, 0, 0)

    def test_feb_29_non_leap_year_rejected(self, handler):
        result = handler.extract_metadata(Path("photo_2021-02-29_12-00-00.jpg"))
        assert result == {}

    def test_allows_suffix_after_timestamp(self, handler):
        # Telegram handler has no end anchor, allowing suffixes
        result = handler.extract_metadata(Path("photo_2024-06-15_14-30-22_copy.jpg"))
        assert result["date"] == datetime(2024, 6, 15, 14, 30, 22)
