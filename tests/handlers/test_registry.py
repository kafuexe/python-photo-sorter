import pytest

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


@pytest.fixture
def registry():
    return HandlerRegistry()


class TestHandlerRegistration:
    def test_register_and_retrieve(self, registry):
        h = StubHandler(["jpg", "png"], 10)
        registry.register(h)

        assert registry.get_handlers("jpg") == [h]
        assert registry.get_handlers("png") == [h]

    def test_unregistered_extension_returns_empty(self, registry):
        registry.register(StubHandler(["jpg"], 10))
        assert registry.get_handlers("mp4") == []

    def test_empty_registry_returns_empty(self, registry):
        assert registry.get_handlers("jpg") == []
        assert registry.get_all_extensions() == set()


class TestHandlerOrdering:
    def test_handlers_sorted_by_priority(self, registry):
        h50 = StubHandler(["jpg"], 50)
        h10 = StubHandler(["jpg"], 10)
        h30 = StubHandler(["jpg"], 30)
        registry.register(h50)
        registry.register(h10)
        registry.register(h30)

        priorities = [h.priority() for h in registry.get_handlers("jpg")]
        assert priorities == [10, 30, 50]


class TestWildcardHandler:
    def test_wildcard_appended_to_specific_handlers(self, registry):
        specific = StubHandler(["jpg"], 10)
        fallback = StubHandler(["*"], 100)
        registry.register(specific)
        registry.register(fallback)

        handlers = registry.get_handlers("jpg")
        assert handlers == [specific, fallback]

    def test_wildcard_serves_unknown_extensions(self, registry):
        fallback = StubHandler(["*"], 100)
        registry.register(fallback)

        assert registry.get_handlers("xyz") == [fallback]

    def test_wildcard_excluded_from_all_extensions(self, registry):
        registry.register(StubHandler(["jpg", "png"], 10))
        registry.register(StubHandler(["*"], 100))

        exts = registry.get_all_extensions()
        assert exts == {"jpg", "png"}
        assert "*" not in exts


class TestExtensionNormalization:
    @pytest.mark.parametrize("query", ["jpg", "JPG", "Jpg"])
    def test_case_insensitive_lookup(self, registry, query):
        registry.register(StubHandler(["JPG"], 10))
        assert len(registry.get_handlers(query)) == 1

    def test_dot_prefix_stripped(self, registry):
        registry.register(StubHandler(["jpg"], 10))
        assert len(registry.get_handlers(".jpg")) == 1

    def test_double_dot_extension(self, registry):
        registry.register(StubHandler(["jpg"], 10))
        # "..jpg" stripped to ".jpg" then to "jpg" — should still match
        assert len(registry.get_handlers("..jpg")) == 1

    def test_empty_string_extension(self, registry):
        registry.register(StubHandler(["jpg"], 10))
        assert registry.get_handlers("") == []


class TestRegistryMultipleHandlers:
    def test_same_handler_for_multiple_extensions(self, registry):
        h = StubHandler(["jpg", "png", "webp"], 10)
        registry.register(h)
        for ext in ["jpg", "png", "webp"]:
            assert registry.get_handlers(ext) == [h]

    def test_multiple_handlers_same_extension_different_priorities(self, registry):
        h1 = StubHandler(["jpg"], 10)
        h2 = StubHandler(["jpg"], 20)
        h3 = StubHandler(["jpg"], 30)
        registry.register(h3)
        registry.register(h1)
        registry.register(h2)
        assert registry.get_handlers("jpg") == [h1, h2, h3]

    def test_get_all_extensions_deduplicates(self, registry):
        registry.register(StubHandler(["jpg", "png"], 10))
        registry.register(StubHandler(["jpg", "mp4"], 20))
        assert registry.get_all_extensions() == {"jpg", "png", "mp4"}
