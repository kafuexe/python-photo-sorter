import logging
import re
from datetime import datetime
from pathlib import Path

from .base import BaseHandler

logger = logging.getLogger(__name__)

_SCREENSHOT_RE = re.compile(
    r"^Screenshot_(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})",
    re.IGNORECASE,
)


class ScreenshotHandler(BaseHandler):
    def supported_extensions(self) -> list[str]:
        return ["png", "jpg", "jpeg"]

    def priority(self) -> int:
        return 10

    def extract_metadata(self, file_path: Path) -> dict:
        match = _SCREENSHOT_RE.match(file_path.stem)
        if not match:
            return {}

        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            hour, minute, second = int(match.group(4)), int(match.group(5)), int(match.group(6))
            return {"date": datetime(year, month, day, hour, minute, second)}
        except ValueError:
            logger.debug("Invalid date in Screenshot filename: %s", file_path.name)
            return {}
