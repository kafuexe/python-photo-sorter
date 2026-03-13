import logging
from datetime import datetime
from pathlib import Path

import exifread

from .base import BaseHandler

logger = logging.getLogger(__name__)

EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"

DATE_TAGS = [
    "EXIF DateTimeOriginal",
    "EXIF DateTimeDigitized",
    "Image DateTime",
]


class ExifReadHandler(BaseHandler):
    def supported_extensions(self) -> list[str]:
        return ["jpg", "jpeg", "png", "tiff", "tif", "webp", "heic"]

    def priority(self) -> int:
        return 20

    def extract_metadata(self, file_path: Path) -> dict:
        try:
            with open(file_path, "rb") as f:
                tags = exifread.process_file(f, details=False)
        except Exception:
            logger.debug("Failed to read EXIF via exifread from %s", file_path.name)
            return {}

        if not tags:
            return {}

        metadata = {}

        for tag_name in DATE_TAGS:
            value = tags.get(tag_name)
            if not value:
                continue
            date = self._parse_date(str(value))
            if date:
                metadata["date"] = date
                break

        subsec = tags.get("EXIF SubSecTimeOriginal")
        if subsec and "date" in metadata:
            metadata["subsecond"] = str(subsec)

        return metadata

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        clean = date_str.strip()[:19]
        try:
            return datetime.strptime(clean, EXIF_DATE_FORMAT)
        except ValueError:
            return None
