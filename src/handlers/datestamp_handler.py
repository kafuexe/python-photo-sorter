import logging
import re
from datetime import datetime
from pathlib import Path

from .base import BaseHandler

logger = logging.getLogger(__name__)

_DATESTAMP_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})[_ ](\d{2})\.(\d{2})\.(\d{2})",
    re.IGNORECASE,
)


class DatestampHandler(BaseHandler):
    def supported_extensions(self) -> list[str]:
        return ["jpg", "jpeg", "png", "mp4"]

    def priority(self) -> int:
        return 15

    def extract_metadata(self, file_path: Path) -> dict:
        match = _DATESTAMP_RE.match(file_path.stem)
        if not match:
            return {}

        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            hour, minute, second = int(match.group(4)), int(match.group(5)), int(match.group(6))
            return {"date": datetime(year, month, day, hour, minute, second)}
        except ValueError:
            logger.debug("Invalid date in datestamp filename: %s", file_path.name)
            return {}
