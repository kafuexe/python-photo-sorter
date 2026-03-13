from pathlib import Path

from src.models.file_result import FileResult
from src.models.processing_config import ProcessingConfig
from src.services.log_service import LogService
from src.services.processing_service import TimingStats


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


def _write_full_log(svc, config, results, stats=None):
    """Helper that exercises the streaming API and returns the log path."""
    path = svc.begin(config)
    for r in results:
        svc.log_result(r)
    svc.finish(results, stats)
    return path


class TestLogService:
    def test_creates_log_dir_and_file(self, tmp_path):
        log_dir = tmp_path / "move-log"
        svc = LogService(log_dir=log_dir)

        config = _make_config()
        results = [_make_result("a.jpg", "success")]

        path = _write_full_log(svc, config, results)

        assert log_dir.exists()
        assert path.exists()
        assert path.parent == log_dir

    def test_filename_contains_action(self, tmp_path):
        svc = LogService(log_dir=tmp_path)

        path = _write_full_log(svc, _make_config(action="copy"), [])
        assert "_copy.txt" in path.name

        path = _write_full_log(svc, _make_config(action="move"), [])
        assert "_move.txt" in path.name

    def test_log_contains_timestamp(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        path = _write_full_log(svc, _make_config(), [])
        content = path.read_text(encoding="utf-8")

        assert "Date:" in content

    def test_log_contains_settings(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        config = _make_config(date_format="%Y-%m", action="copy",
                              selected_extensions=["jpg", "tiff"])
        path = _write_full_log(svc, config, [])
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
        path = _write_full_log(svc, _make_config(), results)
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
        path = _write_full_log(svc, _make_config(), results)
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
        path = _write_full_log(svc, _make_config(), results)
        content = path.read_text(encoding="utf-8")

        assert "permission denied" in content

    def test_log_shows_destination_paths(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        results = [
            _make_result("a.jpg", "success"),
        ]
        path = _write_full_log(svc, _make_config(), results)
        content = path.read_text(encoding="utf-8")

        assert "a.jpg" in content
        assert "->" in content
        # Source and destination both present (path separators vary by OS)
        assert str(Path("/src/a.jpg")) in content
        assert str(Path("/dst/a.jpg")) in content

    def test_empty_results(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        path = _write_full_log(svc, _make_config(), [])
        content = path.read_text(encoding="utf-8")

        assert "Total: 0" in content
        assert "=== Files ===" in content

    def test_multiple_writes_create_separate_files(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        path1 = _write_full_log(svc, _make_config(), [])
        path2 = _write_full_log(svc, _make_config(action="copy"), [])

        assert path1 != path2
        assert len(list(tmp_path.glob("*.txt"))) == 2

    def test_log_includes_timing_when_provided(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        stats = TimingStats(
            find=0.05, extract=1.2, resolve=0.01, execute=0.8,
            total=2.06, file_count=3,
        )
        stats.record("a.jpg", 0.5, 0.005, 0.3)
        stats.record("b.jpg", 0.4, 0.003, 0.2)
        stats.record("c.jpg", 0.3, 0.002, 0.3)

        path = _write_full_log(svc, _make_config(), [], stats)
        content = path.read_text(encoding="utf-8")

        assert "=== Timing ===" in content
        assert "Total time:" in content
        assert "File discovery:" in content
        assert "Metadata extract:" in content
        assert "=== Slowest Files ===" in content
        assert "a.jpg" in content

    def test_log_omits_timing_when_not_provided(self, tmp_path):
        svc = LogService(log_dir=tmp_path)
        path = _write_full_log(svc, _make_config(), [])
        content = path.read_text(encoding="utf-8")

        assert "=== Timing ===" not in content
        assert "=== Slowest Files ===" not in content

    def test_log_result_writes_immediately(self, tmp_path):
        """Each log_result() call flushes to disk right away."""
        svc = LogService(log_dir=tmp_path)
        config = _make_config()
        path = svc.begin(config)

        r1 = _make_result("a.jpg", "success")
        svc.log_result(r1)

        # File on disk should already contain the first result
        content = path.read_text(encoding="utf-8")
        assert "a.jpg" in content
        assert "[SUCCESS]" in content

        r2 = _make_result("b.png", "error", destination=None, error="oops")
        svc.log_result(r2)

        content = path.read_text(encoding="utf-8")
        assert "b.png" in content
        assert "oops" in content

        svc.finish([r1, r2])
