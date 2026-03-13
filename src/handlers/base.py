from abc import ABC, abstractmethod
from pathlib import Path


class BaseHandler(ABC):
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Extensions this handler can process, e.g. ['jpg', 'png'].
        Return ['*'] for a universal fallback handler."""

    @abstractmethod
    def priority(self) -> int:
        """Execution order. Lower = runs first.
        Convention: 10 = native/fast, 50 = external tool, 100 = fallback."""

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> dict:
        """Extract metadata from file. Returns dict with extracted key-value pairs.
        Should include 'date' key (datetime | None) when date extraction is attempted.
        Returns empty dict if nothing could be extracted."""
