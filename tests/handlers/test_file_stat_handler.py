from datetime import datetime
from pathlib import Path

import pytest

from src.handlers.file_stat_handler import FileStatHandler


@pytest.fixture
def handler():
    return FileStatHandler()


class TestFileStatHandlerConfig:
    def test_is_universal_fallback(self, handler):
        assert handler.supported_extensions() == ["*"]

    def test_priority_is_lowest(self, handler):
        assert handler.priority() == 100


class TestFileStatExtraction:
    def test_existing_file_returns_datetime(self, handler, tmp_path):
        path = tmp_path / "file.txt"
        path.write_text("hello")

        result = handler.extract_metadata(path)
        assert isinstance(result["date"], datetime)

    def test_date_is_not_in_the_future(self, handler, tmp_path):
        path = tmp_path / "file.txt"
        path.write_text("hello")

        result = handler.extract_metadata(path)
        assert result["date"] <= datetime.now()

    def test_picks_earlier_of_mtime_and_ctime(self, handler, tmp_path):
        import os
        path = tmp_path / "file.txt"
        path.write_text("hello")
        stat = path.stat()
        earliest = min(stat.st_mtime, stat.st_ctime)
        result = handler.extract_metadata(path)
        assert result["date"] == datetime.fromtimestamp(earliest)

    def test_result_contains_only_date_key(self, handler, tmp_path):
        path = tmp_path / "file.txt"
        path.write_text("hello")
        result = handler.extract_metadata(path)
        assert list(result.keys()) == ["date"]

    def test_nonexistent_file_returns_empty(self, handler, tmp_path):
        result = handler.extract_metadata(tmp_path / "missing.txt")
        assert result == {}
