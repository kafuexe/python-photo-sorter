from pathlib import Path

import pytest

from src.models.file_result import FileResult


@pytest.fixture
def default_result():
    return FileResult(source=Path("photo.jpg"))


class TestFileResultDefaults:
    @pytest.mark.parametrize("attr, expected", [
        ("destination", None),
        ("status", "pending"),
        ("error", None),
        ("metadata", {}),
    ])
    def test_default_values(self, default_result, attr, expected):
        assert getattr(default_result, attr) == expected

    def test_source_preserved(self, default_result):
        assert default_result.source == Path("photo.jpg")


class TestFileResultFields:
    def test_all_fields_assignable(self):
        r = FileResult(
            source=Path("a.jpg"),
            destination=Path("out/a.jpg"),
            status="success",
            error=None,
            metadata={"date": "2024-01-01"},
        )
        assert r.status == "success"
        assert r.destination == Path("out/a.jpg")
        assert r.metadata["date"] == "2024-01-01"

    def test_metadata_default_not_shared_between_instances(self):
        r1 = FileResult(source=Path("a.jpg"))
        r2 = FileResult(source=Path("b.jpg"))
        r1.metadata["key"] = "value"
        assert "key" not in r2.metadata
