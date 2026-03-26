from datetime import datetime
from pathlib import Path

import pytest

from src.handlers.base import BaseHandler
from src.handlers.registry import HandlerRegistry
from src.steps.metadata_extractor import MetadataExtractor, BaseMetadataExtractor


class FakeDateHandler(BaseHandler):
    def __init__(self, extensions, prio, date=None, extra=None):
        self._ext = extensions
        self._prio = prio
        self._date = date
        self._extra = extra or {}

    def supported_extensions(self):
        return self._ext

    def priority(self):
        return self._prio

    def extract_metadata(self, file_path):
        result = dict(self._extra)
        if self._date is not None:
            result["date"] = self._date
        return result


class CrashingHandler(BaseHandler):
    def supported_extensions(self):
        return ["jpg"]

    def priority(self):
        return 5

    def extract_metadata(self, file_path):
        raise RuntimeError("boom")


@pytest.fixture
def registry():
    return HandlerRegistry()


@pytest.fixture
def jpg_file(tmp_path):
    path = tmp_path / "test.jpg"
    path.write_bytes(b"img")
    return path


class TestMetadataExtractorConfig:
    def test_is_subclass_of_base(self):
        assert issubclass(MetadataExtractor, BaseMetadataExtractor)


class TestMetadataExtractorDateResolution:
    def test_first_date_wins(self, registry, jpg_file):
        dt1, dt2 = datetime(2024, 1, 1), datetime(2025, 6, 15)
        registry.register(FakeDateHandler(["jpg"], 10, date=dt1))
        registry.register(FakeDateHandler(["jpg"], 50, date=dt2))

        result = MetadataExtractor(registry).extract(jpg_file)
        assert result["date"] == dt1

    def test_skips_none_date_to_find_valid(self, registry, jpg_file):
        dt = datetime(2024, 1, 1)
        registry.register(FakeDateHandler(["jpg"], 10, date=None))
        registry.register(FakeDateHandler(["jpg"], 50, date=dt))

        result = MetadataExtractor(registry).extract(jpg_file)
        assert result["date"] == dt


class TestMetadataExtractorKeyMerging:
    def test_keys_accumulate_across_handlers(self, registry, jpg_file):
        registry.register(FakeDateHandler(["jpg"], 10, extra={"camera": "Canon"}))
        registry.register(FakeDateHandler(["jpg"], 50, extra={"gps": "12,34"}))

        result = MetadataExtractor(registry).extract(jpg_file)
        assert result["camera"] == "Canon"
        assert result["gps"] == "12,34"

    def test_first_handler_wins_for_duplicate_keys(self, registry, jpg_file):
        registry.register(FakeDateHandler(["jpg"], 10, extra={"camera": "Canon"}))
        registry.register(FakeDateHandler(["jpg"], 50, extra={"camera": "Nikon"}))

        result = MetadataExtractor(registry).extract(jpg_file)
        assert result["camera"] == "Canon"


class TestMetadataExtractorResilience:
    def test_crashing_handler_is_skipped(self, registry, jpg_file):
        dt = datetime(2024, 1, 1)
        registry.register(CrashingHandler())
        registry.register(FakeDateHandler(["jpg"], 50, date=dt))

        result = MetadataExtractor(registry).extract(jpg_file)
        assert result["date"] == dt

    def test_no_handlers_returns_empty(self, registry, tmp_path):
        path = tmp_path / "test.xyz"
        path.write_bytes(b"data")

        result = MetadataExtractor(registry).extract(path)
        assert result == {}

    def test_all_handlers_crash_returns_empty(self, registry, jpg_file):
        registry.register(CrashingHandler())
        result = MetadataExtractor(registry).extract(jpg_file)
        assert result == {}

    def test_handler_returning_empty_dict_skipped(self, registry, jpg_file):
        """A handler that returns {} should not block subsequent handlers."""
        dt = datetime(2024, 1, 1)

        class EmptyHandler(BaseHandler):
            def supported_extensions(self): return ["jpg"]
            def priority(self): return 5
            def extract_metadata(self, fp): return {}

        registry.register(EmptyHandler())
        registry.register(FakeDateHandler(["jpg"], 50, date=dt))

        result = MetadataExtractor(registry).extract(jpg_file)
        assert result["date"] == dt
