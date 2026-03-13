import logging
import shutil
from datetime import datetime
from pathlib import Path

from .base import BaseHandler

logger = logging.getLogger(__name__)

DATE_FORMATS = [
    "%Y:%m:%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y:%m:%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S%z",
]

DATE_TAGS = ["EXIF:DateTimeOriginal", "EXIF:CreateDate", "QuickTime:CreateDate", "CreateDate"]


class PyExifToolHandler(BaseHandler):
    def __init__(self):
        self._available = self._check_availability()
        if not self._available:
            logger.warning(
                "exiftool not found on PATH. PyExifToolHandler will be inactive. "
                "Install exiftool to enable video metadata extraction."
            )

    @staticmethod
    def _check_availability() -> bool:
        return shutil.which("exiftool") is not None

    @property
    def available(self) -> bool:
        return self._available

    def supported_extensions(self) -> list[str]:
        return ["jpg", "jpeg", "png", "webp", "mov", "avi", "mp4", "mkv", "wmv", "flv"]

    def priority(self) -> int:
        return 50

    def extract_metadata(self, file_path: Path) -> dict:
        if not self._available:
            return {}

        try:
            import exiftool

            with exiftool.ExifToolHelper() as et:
                metadata_list = et.get_metadata(str(file_path))
                if not metadata_list:
                    return {}

                raw = metadata_list[0]
        except Exception:
            return {}

        metadata = {}

        for tag in DATE_TAGS:
            value = raw.get(tag)
            if not value:
                continue
            date = self._parse_date(str(value))
            if date:
                metadata["date"] = date
                break

        return metadata

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        clean = date_str.strip()[:19]
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(clean, fmt)
            except ValueError:
                continue
        return None
