from pathlib import Path

from ....handlers.registry import HandlerRegistry
from .base import BaseMetadataExtractor


class MetadataExtractor(BaseMetadataExtractor):
    def __init__(self, registry: HandlerRegistry):
        self._registry = registry

    def extract(self, file_path: Path) -> dict:
        """Run all applicable handlers in priority order.
        First valid 'date' wins. Other keys accumulate."""
        extension = file_path.suffix.lower().lstrip(".")
        handlers = self._registry.get_handlers(extension)

        merged: dict = {}
        for handler in handlers:
            try:
                result = handler.extract_metadata(file_path)
            except Exception:
                continue

            for key, value in result.items():
                if key == "date":
                    if "date" not in merged and value is not None:
                        merged["date"] = value
                else:
                    if key not in merged:
                        merged[key] = value

        return merged
