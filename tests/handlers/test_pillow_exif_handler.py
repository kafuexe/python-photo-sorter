from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image
from PIL.ExifTags import Base as ExifBase

from src.handlers.pillow_exif_handler import PillowExifHandler


@pytest.fixture
def handler():
    return PillowExifHandler()


@pytest.fixture
def image_with_exif(tmp_path):
    """Create a JPEG with a given EXIF DateTimeOriginal."""
    def _create(filename="photo.jpg", date_str="2024:06:15 14:30:00"):
        path = tmp_path / filename
        img = Image.new("RGB", (10, 10))
        exif = img.getexif()
        exif[ExifBase.DateTimeOriginal] = date_str
        img.save(path, exif=exif)
        return path
    return _create


@pytest.fixture
def image_without_exif(tmp_path):
    def _create(filename="noexif.jpg"):
        path = tmp_path / filename
        Image.new("RGB", (10, 10)).save(path)
        return path
    return _create


class TestPillowExifHandlerConfig:
    def test_supports_common_image_formats(self, handler):
        exts = handler.supported_extensions()
        assert set(exts) >= {"jpg", "jpeg", "png", "webp"}

    def test_priority_is_fast_native(self, handler):
        assert handler.priority() == 10


class TestPillowExifExtraction:
    @pytest.mark.parametrize("date_str, expected", [
        ("2024:06:15 14:30:00", datetime(2024, 6, 15, 14, 30, 0)),
        ("2020:01:01 00:00:00", datetime(2020, 1, 1, 0, 0, 0)),
        ("2019:12:31 23:59:59", datetime(2019, 12, 31, 23, 59, 59)),
    ])
    def test_extracts_date_from_exif(self, handler, image_with_exif, date_str, expected):
        path = image_with_exif(date_str=date_str)
        result = handler.extract_metadata(path)
        assert result["date"] == expected


class TestPillowExifFailures:
    @pytest.mark.parametrize("scenario, setup", [
        ("no_exif", "no_exif"),
        ("corrupt_file", "corrupt"),
        ("nonexistent_file", "missing"),
    ])
    def test_returns_empty_on_failure(self, handler, tmp_path, scenario, setup):
        if setup == "no_exif":
            path = tmp_path / "noexif.jpg"
            Image.new("RGB", (10, 10)).save(path)
        elif setup == "corrupt":
            path = tmp_path / "corrupt.jpg"
            path.write_bytes(b"not an image")
        else:
            path = tmp_path / "missing.jpg"

        assert handler.extract_metadata(path) == {}


class TestPillowExifTagFallback:
    def test_falls_back_to_DateTime_when_original_missing(self, handler, tmp_path):
        """When DateTimeOriginal is absent, handler should try DateTime (tag 306)."""
        img = Image.new("RGB", (10, 10))
        exif = img.getexif()
        # Tag 306 = DateTime (third fallback)
        exif[306] = "2022:07:04 12:00:00"
        path = tmp_path / "fallback.jpg"
        img.save(path, exif=exif)

        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2022, 7, 4, 12, 0, 0)

    def test_subsecond_extracted_alongside_date(self, handler, tmp_path):
        img = Image.new("RGB", (10, 10))
        exif = img.getexif()
        exif[ExifBase.DateTimeOriginal] = "2024:06:15 14:30:00"
        exif[37521] = "456"  # SubsecTimeOriginal
        path = tmp_path / "subsec.jpg"
        img.save(path, exif=exif)

        result = handler.extract_metadata(path)
        assert result["date"] == datetime(2024, 6, 15, 14, 30, 0)
        assert result["subsecond"] == "456"

    def test_empty_date_string_skipped(self, handler, tmp_path):
        img = Image.new("RGB", (10, 10))
        exif = img.getexif()
        exif[ExifBase.DateTimeOriginal] = "   "
        path = tmp_path / "empty_date.jpg"
        img.save(path, exif=exif)

        result = handler.extract_metadata(path)
        assert result == {}
