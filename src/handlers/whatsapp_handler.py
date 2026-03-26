import logging
import re
from datetime import datetime
from pathlib import Path

from .base import BaseHandler

logger = logging.getLogger(__name__)

_WHATSAPP_RE = re.compile(
    r"^(?:IMG|VID)-(\d{4})(\d{2})(\d{2})-WA\d+$",
    re.IGNORECASE,
)


class WhatsAppHandler(BaseHandler):
    def supported_extensions(self) -> list[str]:
        return ["jpg", "jpeg", "mp4"]

    def priority(self) -> int:
        return 10

    def extract_metadata(self, file_path: Path) -> dict:
        match = _WHATSAPP_RE.match(file_path.stem)
        if not match:
            return {}

        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return {"date": datetime(year, month, day)}
        except ValueError:
            logger.debug("Invalid date in WhatsApp filename: %s", file_path.name)
            return {}
