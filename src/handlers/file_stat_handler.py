import logging
import os
from datetime import datetime
from pathlib import Path

from .base import BaseHandler

logger = logging.getLogger(__name__)


class FileStatHandler(BaseHandler):
    def supported_extensions(self) -> list[str]:
        return ["*"]

    def priority(self) -> int:
        return 100

    def extract_metadata(self, file_path: Path) -> dict:
        try:
            stat = file_path.stat()
            # Use the earliest available timestamp
            # On Windows, st_ctime is creation time; on Unix, it's metadata change time
            timestamp = min(stat.st_mtime, stat.st_ctime)
            return {"date": datetime.fromtimestamp(timestamp)}
        except (OSError, ValueError):
            logger.debug("Failed to read file stats for %s", file_path.name)
            return {}
