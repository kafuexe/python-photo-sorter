from datetime import datetime
from pathlib import Path

from src.handlers.base import BaseHandler
from src.handlers.registry import HandlerRegistry
from src.services.steps.metadata_extractor import MetadataExtractor, BaseMetadataExtractor


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


class TestMetadataExtractor:
    def test_is_subclass_of_base(self):
        assert issubclass(MetadataExtractor, BaseMetadataExtractor)

    def test_first_date_wins(self, tmp_path):
        path = tmp_path / "test.jpg"
        path.write_bytes(b"img")

        reg = HandlerRegistry()
        dt1 = datetime(2024, 1, 1)
        dt2 = datetime(2025, 6, 15)
        reg.register(FakeDateHandler(["jpg"], 10, date=dt1))
        reg.register(FakeDateHandler(["jpg"], 50, date=dt2))

        result = MetadataExtractor(reg).extract(path)
        assert result["date"] == dt1

    def test_other_keys_accumulate(self, tmp_path):
        path = tmp_path / "test.jpg"
        path.write_bytes(b"img")

        reg = HandlerRegistry()
        reg.register(FakeDateHandler(["jpg"], 10, extra={"camera": "Canon"}))
        reg.register(FakeDateHandler(["jpg"], 50, extra={"gps": "12,34"}))

        result = MetadataExtractor(reg).extract(path)
        assert result["camera"] == "Canon"
        assert result["gps"] == "12,34"

    def test_first_key_wins_for_non_date(self, tmp_path):
        path = tmp_path / "test.jpg"
        path.write_bytes(b"img")

        reg = HandlerRegistry()
        reg.register(FakeDateHandler(["jpg"], 10, extra={"camera": "Canon"}))
        reg.register(FakeDateHandler(["jpg"], 50, extra={"camera": "Nikon"}))

        result = MetadataExtractor(reg).extract(path)
        assert result["camera"] == "Canon"

    def test_skips_none_date(self, tmp_path):
        path = tmp_path / "test.jpg"
        path.write_bytes(b"img")

        reg = HandlerRegistry()
        reg.register(FakeDateHandler(["jpg"], 10, date=None))
        dt = datetime(2024, 1, 1)
        reg.register(FakeDateHandler(["jpg"], 50, date=dt))

        result = MetadataExtractor(reg).extract(path)
        assert result["date"] == dt

    def test_no_handlers_returns_empty(self, tmp_path):
        path = tmp_path / "test.xyz"
        path.write_bytes(b"data")

        reg = HandlerRegistry()
        result = MetadataExtractor(reg).extract(path)
        assert result == {}

    def test_crashing_handler_skipped(self, tmp_path):
        path = tmp_path / "test.jpg"
        path.write_bytes(b"img")

        reg = HandlerRegistry()
        reg.register(CrashingHandler())
        dt = datetime(2024, 1, 1)
        reg.register(FakeDateHandler(["jpg"], 50, date=dt))

        result = MetadataExtractor(reg).extract(path)
        assert result["date"] == dt
