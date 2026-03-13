from pathlib import Path
from src.models.file_result import FileResult


class TestFileResult:
    def test_defaults(self):
        r = FileResult(source=Path("photo.jpg"))
        assert r.source == Path("photo.jpg")
        assert r.destination is None
        assert r.status == "pending"
        assert r.error is None
        assert r.metadata == {}

    def test_all_fields(self):
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

    def test_metadata_default_not_shared(self):
        r1 = FileResult(source=Path("a.jpg"))
        r2 = FileResult(source=Path("b.jpg"))
        r1.metadata["key"] = "value"
        assert "key" not in r2.metadata
