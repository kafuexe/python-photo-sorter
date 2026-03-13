from pathlib import Path

from src.models.file_result import FileResult
from src.models.processing_config import ProcessingConfig
from src.services.log_service import LogService


def _make_config(**overrides) -> ProcessingConfig:
    defaults = dict(
        input_dir=Path("/src"),
        output_dir=Path("/dst"),
        date_format="%Y/%m/%d",
        action="move",
        selected_extensions=["jpg", "png"],
        handle_unknown=True,
    )
    defaults.update(overrides)
    return ProcessingConfig(**defaults)


def _make_result(name, status, destination=None, error=None) -> FileResult:
    r = FileResult(source=Path(f"/src/{name}"))
    r.status = status
    r.destination = Path(f"/dst/{name}") if destination is None and status != "skipped" else destination
    r.error = error
    return r


class TestLogService:
    def test_creates_log_dir_and_file(self, tmp_path):
        log_dir = tmp_path / "move-log"
        svc = LogService(log_dir=log_dir)

        config = _make_config()
        results = [_make_result("a.jpg", "success")]

        path = svc.write(config, results)

        assert log_dir.exists()
        assert path.exists()
        assert path.parent == log_dir

    def test_filename_contains_action(self, tmp_path):
        svc = LogService(log_dir=tmp_path)

        path = svc.write(_make_config(action="copy"), [])
        assert "_copy.txt" in path.name

        path = svc.write(_make_config(action="move"), [])
        assert "_move.txt" in path.name

    def test_log_contains_timestamp(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        path = svc.write(_make_config(), [])
        content = path.read_text(encoding="utf-8")

        assert "Date:" in content

    def test_log_contains_settings(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        config = _make_config(date_format="%Y-%m", action="copy",
                              selected_extensions=["jpg", "tiff"])
        path = svc.write(config, [])
        content = path.read_text(encoding="utf-8")

        assert "=== Settings ===" in content
        assert str(config.input_dir) in content
        assert str(config.output_dir) in content
        assert "%Y-%m" in content
        assert "copy" in content
        assert "jpg" in content
        assert "tiff" in content

    def test_log_contains_summary(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        results = [
            _make_result("a.jpg", "success"),
            _make_result("b.jpg", "success"),
            _make_result("c.png", "skipped"),
            _make_result("d.jpg", "error", destination=None, error="disk full"),
            _make_result("e.jpg", "unknown"),
        ]
        path = svc.write(_make_config(), results)
        content = path.read_text(encoding="utf-8")

        assert "Total: 5" in content
        assert "Success: 2" in content
        assert "Skipped: 1" in content
        assert "Errors: 1" in content
        assert "Unknown: 1" in content

    def test_log_lists_every_file(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        results = [
            _make_result("a.jpg", "success"),
            _make_result("b.png", "skipped"),
        ]
        path = svc.write(_make_config(), results)
        content = path.read_text(encoding="utf-8")

        assert "a.jpg" in content
        assert "b.png" in content
        assert "[SUCCESS]" in content
        assert "[SKIPPED]" in content

    def test_log_includes_error_message(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        results = [
            _make_result("bad.jpg", "error", destination=None, error="permission denied"),
        ]
        path = svc.write(_make_config(), results)
        content = path.read_text(encoding="utf-8")

        assert "permission denied" in content

    def test_log_shows_destination_paths(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        results = [
            _make_result("a.jpg", "success"),
        ]
        path = svc.write(_make_config(), results)
        content = path.read_text(encoding="utf-8")

        assert "a.jpg" in content
        assert "->" in content
        # Source and destination both present (path separators vary by OS)
        assert str(Path("/src/a.jpg")) in content
        assert str(Path("/dst/a.jpg")) in content

    def test_empty_results(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        path = svc.write(_make_config(), [])
        content = path.read_text(encoding="utf-8")

        assert "Total: 0" in content
        assert "=== Files ===" in content

    def test_multiple_writes_create_separate_files(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        path1 = svc.write(_make_config(), [])
        path2 = svc.write(_make_config(action="copy"), [])

        assert path1 != path2
        assert len(list(tmp_path.glob("*.txt"))) == 2
