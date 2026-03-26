import pytest

from src.steps.file_finder import FileFinder, BaseFileFinder


@pytest.fixture
def finder():
    return FileFinder()


@pytest.fixture
def populated_dir(tmp_path):
    """Create a directory with a few files of different types."""
    (tmp_path / "a.jpg").write_bytes(b"img")
    (tmp_path / "b.png").write_bytes(b"img")
    (tmp_path / "c.txt").write_text("text")
    return tmp_path


class TestFileFinderConfig:
    def test_is_subclass_of_base(self):
        assert issubclass(FileFinder, BaseFileFinder)


class TestFileFinderSearch:
    def test_finds_matching_extensions(self, finder, populated_dir):
        results = finder.find(populated_dir, ["jpg", "png"])
        names = {p.name for p in results}
        assert names == {"a.jpg", "b.png"}

    def test_recursive_search(self, finder, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "a.jpg").write_bytes(b"img")
        (sub / "b.jpg").write_bytes(b"img")

        assert len(finder.find(tmp_path, ["jpg"])) == 2

    def test_case_insensitive_extensions(self, finder, tmp_path):
        (tmp_path / "photo.JPG").write_bytes(b"img")
        assert len(finder.find(tmp_path, ["jpg"])) == 1


class TestFileFinderEdgeCases:
    @pytest.mark.parametrize("extensions", [
        ["jpg"],   # no matching files
        [],        # no extensions requested
    ])
    def test_returns_empty_when_nothing_matches(self, finder, tmp_path, extensions):
        (tmp_path / "file.txt").write_text("text")
        assert finder.find(tmp_path, extensions) == []

    def test_nonexistent_directory_returns_empty(self, finder, tmp_path):
        assert finder.find(tmp_path / "nope", ["jpg"]) == []


class TestFileFinderSpecialFiles:
    def test_hidden_files_are_found(self, finder, tmp_path):
        (tmp_path / ".hidden.jpg").write_bytes(b"img")
        results = finder.find(tmp_path, ["jpg"])
        assert len(results) == 1
        assert results[0].name == ".hidden.jpg"

    def test_files_with_no_extension_ignored(self, finder, tmp_path):
        (tmp_path / "Makefile").write_text("all:")
        (tmp_path / "photo.jpg").write_bytes(b"img")
        results = finder.find(tmp_path, ["jpg"])
        assert len(results) == 1

    def test_dot_prefixed_extensions_in_request(self, finder, tmp_path):
        (tmp_path / "photo.jpg").write_bytes(b"img")
        results = finder.find(tmp_path, [".jpg"])
        assert len(results) == 1

    def test_results_are_sorted(self, finder, tmp_path):
        for name in ["c.jpg", "a.jpg", "b.jpg"]:
            (tmp_path / name).write_bytes(b"img")
        results = finder.find(tmp_path, ["jpg"])
        assert [p.name for p in results] == ["a.jpg", "b.jpg", "c.jpg"]
