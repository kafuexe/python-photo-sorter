import logging
import re
from datetime import datetime
from pathlib import Path

from .base import BaseHandler

logger = logging.getLogger(__name__)

_TELEGRAM_RE = re.compile(
    r"^(?:photo|video)_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})",
    re.IGNORECASE,
)


class TelegramHandler(BaseHandler):
    def supported_extensions(self) -> list[str]:
        return ["jpg", "jpeg", "mp4"]

    def priority(self) -> int:
        return 10

    def extract_metadata(self, file_path: Path) -> dict:
        match = _TELEGRAM_RE.match(file_path.stem)
        if not match:
            return {}

        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            hour, minute, second = int(match.group(4)), int(match.group(5)), int(match.group(6))
            return {"date": datetime(year, month, day, hour, minute, second)}
        except ValueError:
            logger.debug("Invalid date in Telegram filename: %s", file_path.name)
            return {}
