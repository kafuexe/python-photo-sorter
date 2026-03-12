import logging

from .base import BaseHandler

logger = logging.getLogger(__name__)


class HandlerRegistry:
    def __init__(self):
        self._handlers: dict[str, list[BaseHandler]] = {}
        self._wildcard_handlers: list[BaseHandler] = []

    def register(self, handler: BaseHandler) -> None:
        extensions = handler.supported_extensions()
        logger.info("Registering handler %s for extensions: %s", type(handler).__name__, extensions)
        for ext in extensions:
            ext = ext.lower()
            if ext == "*":
                self._wildcard_handlers.append(handler)
            else:
                self._handlers.setdefault(ext, []).append(handler)

    def get_handlers(self, extension: str) -> list[BaseHandler]:
        extension = extension.lower().lstrip(".")
        handlers = list(self._handlers.get(extension, []))
        handlers.extend(self._wildcard_handlers)
        handlers.sort(key=lambda h: h.priority())
        return handlers

    def get_all_extensions(self) -> set[str]:
        return set(self._handlers.keys())
