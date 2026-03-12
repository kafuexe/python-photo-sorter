from abc import ABC, abstractmethod
from pathlib import Path


class BaseMetadataExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: Path) -> dict:
        """Extract metadata from a file.

        Args:
            file_path: Path to the file.

        Returns:
            Dict of metadata. Should include 'date' key (datetime | None)
            when date extraction is attempted. Other keys accumulate.
        """
