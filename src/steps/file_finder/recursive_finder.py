import logging
from pathlib import Path

from .base import BaseFileFinder

logger = logging.getLogger(__name__)


class FileFinder(BaseFileFinder):
    def find(self, directory: Path, extensions: list[str]) -> list[Path]:
        """Recursively find files matching given extensions."""
        if not directory.is_dir():
            logger.warning("Directory does not exist: %s", directory)
            return []

        ext_set = {f".{e.lower().lstrip('.')}" for e in extensions}
        results = []

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ext_set:
                results.append(file_path)

        results = sorted(results)
        logger.info("Found %d files in %s", len(results), directory)
        return results
