from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import pytest

from src.handlers.exifread_handler import ExifReadHandler


@pytest.fixture
def handler():
    return ExifReadHandler()


class TestExifReadHandlerConfig:
    def test_supported_extensions(self, handler):
        exts = handler.supported_extensions()
        assert set(exts) >= {"jpg", "jpeg", "png", "tiff", "tif", "webp", "heic"}

    def test_priority(self, handler):
        assert handler.priority() == 20


class TestExifReadDateExtraction:
    @patch("src.handlers.exifread_handler.exifread.process_file")
    def test_extracts_date_from_DateTimeOriginal(self, mock_process, handler, tmp_path):
        path = tmp_path / "photo.jpg"
        path.write_bytes(b"fake")
        mock_process.return_value = {
            "EXIF DateTimeOriginal": "2024:06:15 14:30:00",
        }

        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2024, 6, 15, 14, 30, 0)

    @patch("src.handlers.exifread_handler.exifread.process_file")
    def test_extracts_date_from_DateTimeDigitized_when_original_missing(self, mock_process, handler, tmp_path):
        path = tmp_path / "photo.jpg"
        path.write_bytes(b"fake")
        mock_process.return_value = {
            "EXIF DateTimeDigitized": "2023:03:10 08:00:00",
        }

        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2023, 3, 10, 8, 0, 0)

    @patch("src.handlers.exifread_handler.exifread.process_file")
    def test_extracts_date_from_Image_DateTime_as_last_resort(self, mock_process, handler, tmp_path):
        path = tmp_path / "photo.jpg"
        path.write_bytes(b"fake")
        mock_process.return_value = {
            "Image DateTime": "2020:01:01 00:00:00",
        }

        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2020, 1, 1)

    @patch("src.handlers.exifread_handler.exifread.process_file")
    def test_tag_priority_order_original_wins(self, mock_process, handler, tmp_path):
        path = tmp_path / "photo.jpg"
        path.write_bytes(b"fake")
        mock_process.return_value = {
            "EXIF DateTimeOriginal": "2024:01:01 00:00:00",
            "EXIF DateTimeDigitized": "2025:01:01 00:00:00",
            "Image DateTime": "2026:01:01 00:00:00",
        }

        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2024, 1, 1)

    @patch("src.handlers.exifread_handler.exifread.process_file")
    def test_subsecond_extracted_when_date_present(self, mock_process, handler, tmp_path):
        path = tmp_path / "photo.jpg"
        path.write_bytes(b"fake")
        mock_process.return_value = {
            "EXIF DateTimeOriginal": "2024:06:15 14:30:00",
            "EXIF SubSecTimeOriginal": "123",
        }

        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2024, 6, 15, 14, 30, 0)
        assert result["subsecond"] == "123"

    @patch("src.handlers.exifread_handler.exifread.process_file")
    def test_subsecond_not_set_without_date(self, mock_process, handler, tmp_path):
        path = tmp_path / "photo.jpg"
        path.write_bytes(b"fake")
        mock_process.return_value = {
            "EXIF SubSecTimeOriginal": "123",
        }

        result = handler.extract_metadata(path)
        assert "subsecond" not in result


class TestExifReadFailures:
    @patch("src.handlers.exifread_handler.exifread.process_file")
    def test_empty_tags_returns_empty(self, mock_process, handler, tmp_path):
        path = tmp_path / "photo.jpg"
        path.write_bytes(b"fake")
        mock_process.return_value = {}

        assert handler.extract_metadata(path) == {}

    @patch("src.handlers.exifread_handler.exifread.process_file")
    def test_none_tags_returns_empty(self, mock_process, handler, tmp_path):
        path = tmp_path / "photo.jpg"
        path.write_bytes(b"fake")
        mock_process.return_value = None

        assert handler.extract_metadata(path) == {}

    def test_nonexistent_file_returns_empty(self, handler, tmp_path):
        result = handler.extract_metadata(tmp_path / "missing.jpg")
        assert result == {}

    @patch("src.handlers.exifread_handler.exifread.process_file", side_effect=Exception("boom"))
    def test_exception_during_read_returns_empty(self, mock_process, handler, tmp_path):
        path = tmp_path / "photo.jpg"
        path.write_bytes(b"fake")
        assert handler.extract_metadata(path) == {}

    @patch("src.handlers.exifread_handler.exifread.process_file")
    def test_invalid_date_string_returns_empty(self, mock_process, handler, tmp_path):
        path = tmp_path / "photo.jpg"
        path.write_bytes(b"fake")
        mock_process.return_value = {
            "EXIF DateTimeOriginal": "not a date",
        }

        assert handler.extract_metadata(path) == {}


class TestExifReadParseDate:
    @pytest.mark.parametrize("date_str, expected", [
        ("2024:06:15 14:30:00", datetime(2024, 6, 15, 14, 30, 0)),
        ("2020:01:01 00:00:00", datetime(2020, 1, 1)),
        ("2019:12:31 23:59:59", datetime(2019, 12, 31, 23, 59, 59)),
    ])
    def test_valid_date_strings(self, date_str, expected):
        assert ExifReadHandler._parse_date(date_str) == expected

    @pytest.mark.parametrize("date_str", [
        "not a date",
        "",
        "2024-06-15 14:30:00",  # wrong separator
        "2024:13:01 00:00:00",  # month 13
    ])
    def test_invalid_date_strings_return_none(self, date_str):
        assert ExifReadHandler._parse_date(date_str) is None

    def test_truncates_to_19_chars(self):
        # Extra trailing data after 19 chars should be ignored
        result = ExifReadHandler._parse_date("2024:06:15 14:30:00.123456")
        assert result == datetime(2024, 6, 15, 14, 30, 0)

    def test_strips_whitespace(self):
        result = ExifReadHandler._parse_date("  2024:06:15 14:30:00  ")
        assert result == datetime(2024, 6, 15, 14, 30, 0)
