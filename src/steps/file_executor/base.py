from abc import ABC, abstractmethod
from pathlib import Path


class BaseFileExecutor(ABC):
    @abstractmethod
    def execute(self, source: Path, dest: Path, action: str) -> bool:
        """Execute a file operation.

        Args:
            source: Source file path.
            dest: Destination file path.
            action: "move" or "copy".

        Returns:
            True if the operation was performed, False if skipped.
        """
