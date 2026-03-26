from pathlib import Path

import pytest

from src.steps.file_executor import FileExecutor, BaseFileExecutor


@pytest.fixture
def executor():
    return FileExecutor()


@pytest.fixture
def source_file(tmp_path):
    """Create a source file with known content and return its path."""
    def _create(name="photo.jpg", content=b"image data"):
        path = tmp_path / name
        path.write_bytes(content)
        return path
    return _create


class TestFileExecutorConfig:
    def test_is_subclass_of_base(self):
        assert issubclass(FileExecutor, BaseFileExecutor)


class TestFileExecutorCopyMove:
    @pytest.mark.parametrize("action, source_survives", [
        ("copy", True),
        ("move", False),
    ])
    def test_transfers_file_content(self, executor, source_file, tmp_path, action, source_survives):
        src = source_file()
        dest = tmp_path / "out" / "photo.jpg"

        assert executor.execute(src, dest, action) is True
        assert dest.read_bytes() == b"image data"
        assert src.exists() == source_survives

    def test_creates_nested_parent_dirs(self, executor, source_file, tmp_path):
        src = source_file()
        dest = tmp_path / "a" / "b" / "c" / "photo.jpg"

        executor.execute(src, dest, "copy")
        assert dest.exists()


class TestFileExecutorCollisions:
    def test_skips_when_dest_already_exists(self, executor, tmp_path):
        s1 = tmp_path / "s1.jpg"
        s2 = tmp_path / "s2.jpg"
        s1.write_bytes(b"first")
        s2.write_bytes(b"second")
        dest = tmp_path / "out" / "photo.jpg"

        assert executor.execute(s1, dest, "copy") is True
        assert executor.execute(s2, dest, "copy") is False
        assert dest.read_bytes() == b"first"  # original untouched
        assert s2.exists()  # source not consumed

    def test_no_suffixed_files_created_on_collision(self, executor, tmp_path):
        dest = tmp_path / "out" / "photo.jpg"

        for i in range(3):
            src = tmp_path / f"s{i}.jpg"
            src.write_bytes(f"data{i}".encode())
            executor.execute(src, dest, "copy")

        out_dir = tmp_path / "out"
        assert list(out_dir.iterdir()) == [dest]


class TestFileExecutorEdgeCases:
    def test_unknown_action_defaults_to_copy(self, executor, source_file, tmp_path):
        """Non-move action falls through to copy2 (the else branch)."""
        src = source_file()
        dest = tmp_path / "out" / "photo.jpg"

        assert executor.execute(src, dest, "unknown_action") is True
        assert dest.read_bytes() == b"image data"
        assert src.exists()  # not moved, just copied

    def test_copy_preserves_content_integrity(self, executor, tmp_path):
        """Verify copy2 preserves exact bytes for larger content."""
        content = bytes(range(256)) * 100
        src = tmp_path / "large.bin"
        src.write_bytes(content)
        dest = tmp_path / "out" / "large.bin"

        executor.execute(src, dest, "copy")
        assert dest.read_bytes() == content

    def test_dest_is_directory_skips(self, executor, source_file, tmp_path):
        """If dest path already exists as a directory, exists() returns True → skip."""
        src = source_file()
        dest = tmp_path / "out" / "photo.jpg"
        dest.mkdir(parents=True)  # dest is a directory, not a file

        assert executor.execute(src, dest, "copy") is False
