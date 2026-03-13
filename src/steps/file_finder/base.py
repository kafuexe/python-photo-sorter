from abc import ABC, abstractmethod
from pathlib import Path


class BaseFileFinder(ABC):
    @abstractmethod
    def find(self, directory: Path, extensions: list[str]) -> list[Path]:
        """Find files to process.

        Args:
            directory: Root directory to search.
            extensions: File extensions to match (without dot).

        Returns:
            List of matching file paths.
        """
