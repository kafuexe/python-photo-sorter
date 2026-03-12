import struct
import tempfile
from datetime import datetime
from pathlib import Path

from PIL import Image

from src.handlers.pillow_exif_handler import PillowExifHandler


class TestPillowExifHandler:
    def test_supported_extensions(self):
        h = PillowExifHandler()
        exts = h.supported_extensions()
        assert "jpg" in exts
        assert "jpeg" in exts
        assert "png" in exts
        assert "webp" in exts

    def test_priority(self):
        assert PillowExifHandler().priority() == 10

    def test_extract_date_from_exif(self, tmp_path):
        img = Image.new("RGB", (10, 10))
        from PIL.ExifTags import Base as ExifBase
        exif = img.getexif()
        exif[ExifBase.DateTimeOriginal] = "2024:06:15 14:30:00"
        path = tmp_path / "photo.jpg"
        img.save(path, exif=exif)

        result = PillowExifHandler().extract_metadata(path)
        assert "date" in result
        assert result["date"] == datetime(2024, 6, 15, 14, 30, 0)

    def test_no_exif_returns_empty(self, tmp_path):
        img = Image.new("RGB", (10, 10))
        path = tmp_path / "noexif.jpg"
        img.save(path)

        result = PillowExifHandler().extract_metadata(path)
        assert result == {}

    def test_corrupt_file_returns_empty(self, tmp_path):
        path = tmp_path / "corrupt.jpg"
        path.write_bytes(b"not an image")

        result = PillowExifHandler().extract_metadata(path)
        assert result == {}

    def test_nonexistent_file_returns_empty(self, tmp_path):
        path = tmp_path / "missing.jpg"
        result = PillowExifHandler().extract_metadata(path)
        assert result == {}
