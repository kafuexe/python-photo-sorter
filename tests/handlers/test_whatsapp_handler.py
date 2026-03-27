from datetime import datetime
from pathlib import Path

import pytest

from src.handlers.whatsapp_handler import WhatsAppHandler


@pytest.fixture
def handler():
    return WhatsAppHandler()


class TestWhatsAppHandlerConfig:
    def test_supported_extensions_include_common_whatsapp_types(self, handler):
        exts = handler.supported_extensions()
        assert set(exts) >= {"jpg", "jpeg", "mp4"}

    def test_priority_is_fast_native(self, handler):
        assert handler.priority() == 10


class TestWhatsAppDateExtraction:
    @pytest.mark.parametrize(
        "filename, expected_date",
        [
            # standard image filenames
            ("IMG-20210601-WA0001.jpg", datetime(2021, 6, 1)),
            ("IMG-20200315-WA0099.jpeg", datetime(2020, 3, 15)),
            # standard video filenames
            ("VID-20230423-WA0041.mp4", datetime(2023, 4, 23)),
            # single-digit day/month
            ("IMG-20190101-WA0000.jpg", datetime(2019, 1, 1)),
            # end of year
            ("VID-20201231-WA0500.mp4", datetime(2020, 12, 31)),
            # case variations
            ("img-20210601-WA0001.jpg", datetime(2021, 6, 1)),
            ("vid-20230423-wa0041.mp4", datetime(2023, 4, 23)),
            ("Img-20210601-Wa0001.jpg", datetime(2021, 6, 1)),
        ],
        ids=lambda v: v if isinstance(v, str) else "",
    )
    def test_extracts_date_from_whatsapp_filename(self, handler, filename, expected_date):
        result = handler.extract_metadata(Path(filename))
        assert result["date"] == expected_date

    def test_result_contains_only_date_key(self, handler):
        result = handler.extract_metadata(Path("IMG-20210601-WA0001.jpg"))
        assert list(result.keys()) == ["date"]


class TestWhatsAppRejection:
    @pytest.mark.parametrize(
        "filename",
        [
            # not a whatsapp name at all
            "holiday_photo.jpg",
            "screenshot_2023.png",
            # missing WA suffix
            "IMG-20210601-0001.jpg",
            # missing prefix
            "20210601-WA0001.jpg",
            # invalid dates
            "IMG-20211301-WA0001.jpg",  # month 13
            "IMG-20210631-WA0001.jpg",  # june 31
            "IMG-20210000-WA0001.jpg",  # month 0
            # wrong separators
            "IMG_20210601_WA0001.jpg",
            "IMG20210601WA0001.jpg",
            # truncated date
            "IMG-202106-WA0001.jpg",
        ],
        ids=lambda v: v,
    )
    def test_non_whatsapp_or_invalid_returns_empty(self, handler, filename):
        result = handler.extract_metadata(Path(filename))
        assert result == {}

    def test_file_need_not_exist(self, handler):
        path = Path("/nonexistent/dir/VID-20220101-WA0005.mp4")
        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2022, 1, 1)


class TestWhatsAppEdgeCases:
    def test_feb_29_leap_year_valid(self, handler):
        result = handler.extract_metadata(Path("IMG-20200229-WA0001.jpg"))
        assert result["date"] == datetime(2020, 2, 29)

    def test_feb_29_non_leap_year_rejected(self, handler):
        result = handler.extract_metadata(Path("IMG-20210229-WA0001.jpg"))
        assert result == {}

    def test_high_wa_number(self, handler):
        result = handler.extract_metadata(Path("IMG-20210601-WA9999.jpg"))
        assert result["date"] == datetime(2021, 6, 1)

    def test_extra_text_after_wa_number_rejected(self, handler):
        result = handler.extract_metadata(Path("IMG-20210601-WA0001_edited.jpg"))
        assert result == {}
