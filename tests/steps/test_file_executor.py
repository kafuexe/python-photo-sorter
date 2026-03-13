from pathlib import Path

from src.services.steps.file_executor import FileExecutor, BaseFileExecutor


class TestFileExecutor:
    def test_is_subclass_of_base(self):
        assert issubclass(FileExecutor, BaseFileExecutor)

    def test_copy(self, tmp_path):
        src = tmp_path / "photo.jpg"
        src.write_bytes(b"image data")
        dest = tmp_path / "out" / "photo.jpg"

        FileExecutor().execute(src, dest, "copy")

        assert dest.exists()
        assert dest.read_bytes() == b"image data"
        assert src.exists()  # original still there

    def test_move(self, tmp_path):
        src = tmp_path / "photo.jpg"
        src.write_bytes(b"image data")
        dest = tmp_path / "out" / "photo.jpg"

        FileExecutor().execute(src, dest, "move")

        assert dest.exists()
        assert dest.read_bytes() == b"image data"
        assert not src.exists()  # original gone

    def test_creates_parent_dirs(self, tmp_path):
        src = tmp_path / "photo.jpg"
        src.write_bytes(b"data")
        dest = tmp_path / "a" / "b" / "c" / "photo.jpg"

        FileExecutor().execute(src, dest, "copy")
        assert dest.exists()

    def test_collision_appends_suffix(self, tmp_path):
        src1 = tmp_path / "s1.jpg"
        src2 = tmp_path / "s2.jpg"
        src1.write_bytes(b"first")
        src2.write_bytes(b"second")

        dest = tmp_path / "out" / "photo.jpg"
        ex = FileExecutor()
        ex.execute(src1, dest, "copy")
        ex.execute(src2, dest, "copy")

        assert dest.exists()
        assert dest.read_bytes() == b"first"
        collision = tmp_path / "out" / "photo (2).jpg"
        assert collision.exists()
        assert collision.read_bytes() == b"second"

    def test_multiple_collisions(self, tmp_path):
        dest = tmp_path / "out" / "photo.jpg"
        ex = FileExecutor()

        for i in range(4):
            src = tmp_path / f"s{i}.jpg"
            src.write_bytes(f"data{i}".encode())
            ex.execute(src, dest, "copy")

        assert (tmp_path / "out" / "photo.jpg").exists()
        assert (tmp_path / "out" / "photo (2).jpg").exists()
        assert (tmp_path / "out" / "photo (3).jpg").exists()
        assert (tmp_path / "out" / "photo (4).jpg").exists()
