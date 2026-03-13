from datetime import datetime
from pathlib import Path

from src.handlers.file_stat_handler import FileStatHandler


class TestFileStatHandler:
    def test_supported_extensions(self):
        assert FileStatHandler().supported_extensions() == ["*"]

    def test_priority(self):
        assert FileStatHandler().priority() == 100

    def test_extract_returns_date(self, tmp_path):
        path = tmp_path / "file.txt"
        path.write_text("hello")

        result = FileStatHandler().extract_metadata(path)
        assert "date" in result
        assert isinstance(result["date"], datetime)

    def test_nonexistent_file_returns_empty(self, tmp_path):
        path = tmp_path / "missing.txt"
        result = FileStatHandler().extract_metadata(path)
        assert result == {}
