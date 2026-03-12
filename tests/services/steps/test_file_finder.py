from src.services.steps.file_finder import FileFinder


class TestFileFinder:
    def test_finds_matching_files(self, tmp_path):
        (tmp_path / "a.jpg").write_bytes(b"img")
        (tmp_path / "b.png").write_bytes(b"img")
        (tmp_path / "c.txt").write_text("text")

        results = FileFinder().find(tmp_path, ["jpg", "png"])
        names = {p.name for p in results}
        assert names == {"a.jpg", "b.png"}

    def test_recursive(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "a.jpg").write_bytes(b"img")
        (sub / "b.jpg").write_bytes(b"img")

        results = FileFinder().find(tmp_path, ["jpg"])
        assert len(results) == 2

    def test_case_insensitive_extensions(self, tmp_path):
        (tmp_path / "photo.JPG").write_bytes(b"img")

        results = FileFinder().find(tmp_path, ["jpg"])
        assert len(results) == 1

    def test_no_matches(self, tmp_path):
        (tmp_path / "file.txt").write_text("text")

        results = FileFinder().find(tmp_path, ["jpg"])
        assert results == []

    def test_nonexistent_directory(self, tmp_path):
        results = FileFinder().find(tmp_path / "nope", ["jpg"])
        assert results == []

    def test_empty_extensions(self, tmp_path):
        (tmp_path / "a.jpg").write_bytes(b"img")
        results = FileFinder().find(tmp_path, [])
        assert results == []
