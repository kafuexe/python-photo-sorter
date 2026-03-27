import logging
from datetime import datetime
from pathlib import Path

from .base import BaseHandler

logger = logging.getLogger(__name__)

_DATE_FIELDS = ("Tagged_Date", "Encoded_Date", "File_Modified_Date")


class PyMediaInfoHandler(BaseHandler):
    def __init__(self):
        self._available = False
        try:
            from pymediainfo import MediaInfo

            if MediaInfo.can_parse():
                self._available = True
            else:
                logger.warning(
                    "pymediainfo native library not available; video metadata extraction disabled"
                )
        except ImportError:
            logger.warning(
                "pymediainfo not installed; video metadata extraction disabled"
            )
        except Exception as e:
            logger.warning(
                "pymediainfo initialization failed: %s; video metadata extraction disabled",
                e,
            )

    def supported_extensions(self) -> list[str]:
        return ["mp4", "mov", "avi", "mkv", "wmv", "flv", "3gp", "webm"]

    def priority(self) -> int:
        return 50

    def extract_metadata(self, file_path: Path) -> dict:
        if not self._available:
            return {}

        try:
            from pymediainfo import MediaInfo

            media_info = MediaInfo.parse(str(file_path))

            for track in media_info.tracks:
                if track.track_type != "General":
                    continue

                for field in _DATE_FIELDS:
                    value = getattr(track, field, None)
                    if value:
                        parsed = self._parse_date(value)
                        if parsed:
                            return {"date": parsed}

            return {}

        except Exception as e:
            logger.debug("Failed to parse media info for %s: %s", file_path, e)
            return {}

    @staticmethod
    def _parse_date(date_str: str) -> datetime | None:
        """Parse MediaInfo date string, stripping UTC prefix if present."""
        date_str = date_str.strip()
        if date_str.startswith("UTC "):
            date_str = date_str[4:]

        try:
            return datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
