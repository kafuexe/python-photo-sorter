import logging
import shutil
from pathlib import Path

from .base import BaseFileExecutor

logger = logging.getLogger(__name__)


class FileExecutor(BaseFileExecutor):
    def execute(self, source: Path, dest: Path, action: str) -> bool:
        """Move or copy file. Creates parent directories as needed.
        Returns False if destination already exists (skip)."""
        if dest.exists():
            logger.debug("Skipped (exists): %s", dest)
            return False

        dest.parent.mkdir(parents=True, exist_ok=True)

        if action == "move":
            shutil.move(str(source), str(dest))
        else:
            shutil.copy2(str(source), str(dest))

        logger.debug("%s: %s -> %s", action.capitalize(), source, dest)
        return True
