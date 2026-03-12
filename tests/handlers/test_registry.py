from pathlib import Path
from src.handlers.base import BaseHandler
from src.handlers.registry import HandlerRegistry


class StubHandler(BaseHandler):
    def __init__(self, extensions, prio):
        self._extensions = extensions
        self._priority = prio

    def supported_extensions(self):
        return self._extensions

    def priority(self):
        return self._priority

    def extract_metadata(self, file_path):
        return {"handler": type(self).__name__}


class TestHandlerRegistry:
    def test_register_and_get(self):
        reg = HandlerRegistry()
        h = StubHandler(["jpg", "png"], 10)
        reg.register(h)

        assert reg.get_handlers("jpg") == [h]
        assert reg.get_handlers("png") == [h]
        assert reg.get_handlers("mp4") == []

    def test_priority_ordering(self):
        reg = HandlerRegistry()
        h1 = StubHandler(["jpg"], 50)
        h2 = StubHandler(["jpg"], 10)
        h3 = StubHandler(["jpg"], 30)
        reg.register(h1)
        reg.register(h2)
        reg.register(h3)

        handlers = reg.get_handlers("jpg")
        priorities = [h.priority() for h in handlers]
        assert priorities == [10, 30, 50]

    def test_wildcard_handler(self):
        reg = HandlerRegistry()
        specific = StubHandler(["jpg"], 10)
        fallback = StubHandler(["*"], 100)
        reg.register(specific)
        reg.register(fallback)

        jpg_handlers = reg.get_handlers("jpg")
        assert len(jpg_handlers) == 2
        assert jpg_handlers[0] == specific
        assert jpg_handlers[1] == fallback

        # Unknown extension still gets wildcard
        xyz_handlers = reg.get_handlers("xyz")
        assert len(xyz_handlers) == 1
        assert xyz_handlers[0] == fallback

    def test_get_all_extensions_excludes_wildcard(self):
        reg = HandlerRegistry()
        reg.register(StubHandler(["jpg", "png"], 10))
        reg.register(StubHandler(["*"], 100))

        exts = reg.get_all_extensions()
        assert exts == {"jpg", "png"}
        assert "*" not in exts

    def test_case_insensitive(self):
        reg = HandlerRegistry()
        reg.register(StubHandler(["JPG"], 10))

        assert len(reg.get_handlers("jpg")) == 1
        assert len(reg.get_handlers("JPG")) == 1

    def test_dot_prefix_stripped(self):
        reg = HandlerRegistry()
        reg.register(StubHandler(["jpg"], 10))

        assert len(reg.get_handlers(".jpg")) == 1

    def test_empty_registry(self):
        reg = HandlerRegistry()
        assert reg.get_handlers("jpg") == []
        assert reg.get_all_extensions() == set()
