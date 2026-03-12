from abc import ABC, abstractmethod
from pathlib import Path

from ....models.processing_config import ProcessingConfig


class BaseDestinationResolver(ABC):
    @abstractmethod
    def resolve(self, file_path: Path, metadata: dict,
                config: ProcessingConfig) -> Path | None:
        """Determine destination path for a file.

        Args:
            file_path: Source file path.
            metadata: Extracted metadata dict.
            config: Processing configuration.

        Returns:
            Destination path, or None to skip the file.
        """
