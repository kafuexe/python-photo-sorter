import logging
from pathlib import Path

from ...handlers.registry import HandlerRegistry
from .base import BaseMetadataExtractor

logger = logging.getLogger(__name__)


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
                logger.debug("Handler %s failed for %s", type(handler).__name__, file_path)
                continue

            for key, value in result.items():
                if key == "date":
                    if "date" not in merged and value is not None:
                        merged["date"] = value
                else:
                    if key not in merged:
                        merged[key] = value

        if "date" in merged:
            logger.debug("Extracted date %s from %s", merged["date"], file_path.name)
        else:
            logger.debug("No date found for %s", file_path.name)

        return merged
