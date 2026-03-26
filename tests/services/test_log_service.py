from pathlib import Path

import pytest

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


@pytest.fixture
def log_service(tmp_path):
    return LogService(log_dir=tmp_path)


@pytest.fixture
def write_log(log_service):
    """Helper that exercises the streaming API and returns the log path."""
    def _write(config=None, results=None, stats=None):
        config = config or _make_config()
        results = results or []
        path = log_service.begin(config)
        for r in results:
            log_service.log_result(r)
        log_service.finish(results, stats)
        return path
    return _write


class TestLogServiceFileCreation:
    def test_creates_log_dir_and_file(self, tmp_path, log_service, write_log):
        log_dir = tmp_path
        path = write_log()
        assert log_dir.exists()
        assert path.exists()
        assert path.parent == log_dir

    @pytest.mark.parametrize("action, expected_suffix", [
        ("copy", "_copy.txt"),
        ("move", "_move.txt"),
    ])
    def test_filename_reflects_action(self, write_log, action, expected_suffix):
        path = write_log(config=_make_config(action=action))
        assert path.name.endswith(expected_suffix)

    def test_multiple_writes_create_separate_files(self, write_log, tmp_path):
        path1 = write_log()
        path2 = write_log(config=_make_config(action="copy"))
        assert path1 != path2
        assert len(list(tmp_path.glob("*.txt"))) == 2


class TestLogServiceContent:
    def test_contains_timestamp(self, write_log):
        content = write_log().read_text(encoding="utf-8")
        assert "Date:" in content

    @pytest.mark.parametrize("expected_text", [
        "=== Settings ===",
        "%Y-%m",
        "copy",
        "jpg",
        "tiff",
    ])
    def test_contains_settings(self, write_log, expected_text):
        config = _make_config(date_format="%Y-%m", action="copy",
                              selected_extensions=["jpg", "tiff"])
        content = write_log(config=config).read_text(encoding="utf-8")
        assert expected_text in content

    def test_contains_source_and_destination_paths(self, write_log):
        results = [_make_result("a.jpg", "success")]
        content = write_log(results=results).read_text(encoding="utf-8")

        assert str(Path("/src/a.jpg")) in content
        assert "->" in content
        assert str(Path("/dst/a.jpg")) in content

    def test_contains_error_message(self, write_log):
        results = [_make_result("bad.jpg", "error", destination=None, error="permission denied")]
        content = write_log(results=results).read_text(encoding="utf-8")
        assert "permission denied" in content


class TestLogServiceSummary:
    @pytest.fixture
    def mixed_results(self):
        return [
            _make_result("a.jpg", "success"),
            _make_result("b.jpg", "success"),
            _make_result("c.png", "skipped"),
            _make_result("d.jpg", "error", destination=None, error="disk full"),
            _make_result("e.jpg", "unknown"),
        ]

    @pytest.mark.parametrize("label, count", [
        ("Total: 5", None),
        ("Success: 2", None),
        ("Skipped: 1", None),
        ("Errors: 1", None),
        ("Unknown: 1", None),
    ])
    def test_summary_counts(self, write_log, mixed_results, label, count):
        content = write_log(results=mixed_results).read_text(encoding="utf-8")
        assert label in content

    @pytest.mark.parametrize("status_label", ["[SUCCESS]", "[SKIPPED]"])
    def test_status_labels_present(self, write_log, status_label):
        results = [
            _make_result("a.jpg", "success"),
            _make_result("b.png", "skipped"),
        ]
        content = write_log(results=results).read_text(encoding="utf-8")
        assert status_label in content

    def test_empty_results(self, write_log):
        content = write_log().read_text(encoding="utf-8")
        assert "Total: 0" in content
        assert "=== Files ===" in content


class TestLogServiceTiming:
    @pytest.fixture
    def timing_stats(self):
        stats = TimingStats(
            find=0.05, extract=1.2, resolve=0.01, execute=0.8,
            total=2.06, file_count=3,
        )
        stats.record("a.jpg", 0.5, 0.005, 0.3)
        stats.record("b.jpg", 0.4, 0.003, 0.2)
        stats.record("c.jpg", 0.3, 0.002, 0.3)
        return stats

    @pytest.mark.parametrize("expected_text", [
        "=== Timing ===",
        "Total time:",
        "File discovery:",
        "Metadata extract:",
        "=== Slowest Files ===",
    ])
    def test_includes_timing_sections(self, write_log, timing_stats, expected_text):
        content = write_log(stats=timing_stats).read_text(encoding="utf-8")
        assert expected_text in content

    def test_omits_timing_when_not_provided(self, write_log):
        content = write_log().read_text(encoding="utf-8")
        assert "=== Timing ===" not in content


class TestLogServiceStreaming:
    def test_log_result_writes_immediately(self, log_service):
        config = _make_config()
        path = log_service.begin(config)

        r1 = _make_result("a.jpg", "success")
        log_service.log_result(r1)
        content = path.read_text(encoding="utf-8")
        assert "a.jpg" in content
        assert "[SUCCESS]" in content

        r2 = _make_result("b.png", "error", destination=None, error="oops")
        log_service.log_result(r2)
        content = path.read_text(encoding="utf-8")
        assert "b.png" in content
        assert "oops" in content

        log_service.finish([r1, r2])


class TestLogServiceSafety:
    def test_log_result_before_begin_is_noop(self, log_service):
        """Calling log_result without begin() should not raise."""
        log_service.log_result(_make_result("a.jpg", "success"))

    def test_finish_before_begin_is_noop(self, log_service):
        """Calling finish without begin() should not raise."""
        log_service.finish([])

    def test_unicode_filenames_in_log(self, write_log):
        results = [_make_result("фото.jpg", "success")]
        content = write_log(results=results).read_text(encoding="utf-8")
        assert "фото.jpg" in content

    def test_skipped_result_shows_dash_for_destination(self, write_log):
        results = [_make_result("skip.jpg", "skipped")]
        content = write_log(results=results).read_text(encoding="utf-8")
        assert "->  -" in content
