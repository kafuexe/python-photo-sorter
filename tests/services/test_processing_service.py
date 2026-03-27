import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.models.processing_config import ProcessingConfig
from src.services.processing_service import ProcessingService


def make_config(tmp_path, **overrides):
    defaults = {
        "input_dir": tmp_path / "input",
        "output_dir": tmp_path / "output",
        "date_format": "%Y/%m/%d",
        "action": "copy",
        "selected_extensions": ["jpg"],
        "handle_unknown": True,
    }
    defaults.update(overrides)
    return ProcessingConfig(**defaults)


@pytest.fixture
def pipeline():
    """Return (service, finder, extractor, resolver, executor) with MagicMock steps."""
    finder = MagicMock()
    extractor = MagicMock()
    resolver = MagicMock()
    executor = MagicMock()

    finder.find.return_value = []
    extractor.extract.return_value = {}
    resolver.resolve.return_value = None

    service = ProcessingService(
        file_finder=finder,
        metadata_extractor=extractor,
        destination_resolver=resolver,
        file_executor=executor,
    )
    return service, finder, extractor, resolver, executor


class TestProcessingServiceResults:
    def test_empty_directory(self, pipeline, tmp_path):
        service, finder, _, _, _ = pipeline
        config = make_config(tmp_path)

        results, _ = service.process(config)
        assert results == []
        finder.find.assert_called_once()

    def test_successful_processing(self, pipeline, tmp_path):
        service, finder, extractor, resolver, executor = pipeline
        src = Path("/in/photo.jpg")
        dest = Path("/out/2024/01/01/photo.jpg")

        finder.find.return_value = [src]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = dest

        results, _ = service.process(make_config(tmp_path))

        assert len(results) == 1
        assert results[0].status == "success"
        assert results[0].destination == dest
        executor.execute.assert_called_once_with(src, dest, "copy")

    @pytest.mark.parametrize("handle_unknown, dest, expected_status", [
        (False, None,                          "skipped"),
        (True,  Path("/out/.unknown/photo.jpg"), "unknown"),
    ])
    def test_no_date_handling(self, pipeline, tmp_path, handle_unknown, dest, expected_status):
        service, finder, extractor, resolver, executor = pipeline
        finder.find.return_value = [Path("/in/photo.jpg")]
        extractor.extract.return_value = {}
        resolver.resolve.return_value = dest

        results, _ = service.process(make_config(tmp_path, handle_unknown=handle_unknown))

        assert results[0].status == expected_status
        if expected_status == "skipped":
            executor.execute.assert_not_called()

    def test_error_handling(self, pipeline, tmp_path):
        service, finder, extractor, resolver, executor = pipeline
        finder.find.return_value = [Path("/in/photo.jpg")]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = Path("/out/photo.jpg")
        executor.execute.side_effect = OSError("disk full")

        results, _ = service.process(make_config(tmp_path))

        assert results[0].status == "error"
        assert "disk full" in results[0].error

    def test_extractor_exception_produces_error_result(self, pipeline, tmp_path):
        service, finder, extractor, _, _ = pipeline
        finder.find.return_value = [Path("/in/photo.jpg")]
        extractor.extract.side_effect = RuntimeError("corrupt file")

        results, _ = service.process(make_config(tmp_path))

        assert results[0].status == "error"
        assert "corrupt file" in results[0].error

    def test_resolver_exception_produces_error_result(self, pipeline, tmp_path):
        service, finder, extractor, resolver, _ = pipeline
        finder.find.return_value = [Path("/in/photo.jpg")]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.side_effect = ValueError("bad format")

        results, _ = service.process(make_config(tmp_path))

        assert results[0].status == "error"
        assert "bad format" in results[0].error

    def test_executor_returns_false_means_skipped(self, pipeline, tmp_path):
        service, finder, extractor, resolver, executor = pipeline
        finder.find.return_value = [Path("/in/photo.jpg")]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = Path("/out/2024/photo.jpg")
        executor.execute.return_value = False

        results, _ = service.process(make_config(tmp_path))
        assert results[0].status == "skipped"

    def test_metadata_stores_on_result(self, pipeline, tmp_path):
        service, finder, extractor, resolver, _ = pipeline
        dt = datetime(2024, 1, 1)
        finder.find.return_value = [Path("/in/photo.jpg")]
        extractor.extract.return_value = {"date": dt, "camera": "Canon"}
        resolver.resolve.return_value = Path("/out/photo.jpg")

        results, _ = service.process(make_config(tmp_path))
        assert results[0].metadata["date"] == dt
        assert results[0].metadata["camera"] == "Canon"


class TestProcessingServiceCallbacks:
    def test_progress_callback_called_per_file(self, pipeline, tmp_path):
        service, finder, extractor, resolver, _ = pipeline
        finder.find.return_value = [Path(f"/in/{c}.jpg") for c in "ab"]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = Path("/out/photo.jpg")

        progress = []
        results, _ = service.process(make_config(tmp_path), on_progress=progress.append)

        assert len(progress) == 2
        assert len(results) == 2

    def test_multiple_files_all_processed(self, pipeline, tmp_path):
        service, finder, extractor, resolver, _ = pipeline
        finder.find.return_value = [Path(f"/in/photo{i}.jpg") for i in range(5)]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = Path("/out/photo.jpg")

        results, _ = service.process(make_config(tmp_path))
        assert len(results) == 5

    def test_on_total_callback_receives_file_count(self, pipeline, tmp_path):
        service, finder, extractor, resolver, _ = pipeline
        finder.find.return_value = [Path(f"/in/{c}.jpg") for c in "abc"]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = Path("/out/photo.jpg")

        totals = []
        service.process(make_config(tmp_path), on_total=totals.append)
        assert totals == [3]

    def test_on_total_not_called_when_none(self, pipeline, tmp_path):
        service, finder, _, _, _ = pipeline
        finder.find.return_value = [Path("/in/a.jpg")]
        # Should not raise even though on_total is None
        service.process(make_config(tmp_path), on_total=None)


class TestProcessingServiceTiming:
    @pytest.fixture
    def timed_pipeline(self, pipeline, tmp_path):
        """Pipeline with 3 files that produces timing stats."""
        service, finder, extractor, resolver, _ = pipeline
        finder.find.return_value = [Path(f"/in/photo{i}.jpg") for i in range(3)]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = Path("/out/photo.jpg")
        return service, make_config(tmp_path)

    def test_returns_timing_stats(self, timed_pipeline):
        service, config = timed_pipeline
        _, stats = service.process(config)

        assert stats.file_count == 3
        assert stats.total > 0
        assert len(stats.per_file) == 3

    @pytest.mark.parametrize("field", ["find", "extract", "resolve", "execute"])
    def test_timing_fields_are_non_negative(self, timed_pipeline, field):
        service, config = timed_pipeline
        _, stats = service.process(config)
        assert getattr(stats, field) >= 0

    def test_summary_contains_expected_sections(self, timed_pipeline):
        service, config = timed_pipeline
        _, stats = service.process(config)
        summary = stats.summary()

        for label in ("Total time:", "File discovery:", "Metadata extract:", "File execute:"):
            assert label in summary

    def test_slowest_returns_sorted_and_capped(self, timed_pipeline):
        service, config = timed_pipeline
        _, stats = service.process(config)
        slowest = stats.slowest(2)

        assert len(slowest) <= 2
        if len(slowest) == 2:
            total = lambda s: s["extract"] + s["resolve"] + s["execute"]
            assert total(slowest[0]) >= total(slowest[1])

    def test_empty_run_produces_valid_stats(self, pipeline, tmp_path):
        service, _, _, _, _ = pipeline
        _, stats = service.process(make_config(tmp_path))

        assert stats.file_count == 0
        assert stats.total >= 0
        assert stats.per_file == []
        assert stats.slowest(5) == []


class TestProcessingServiceDryRun:
    def test_dry_run_skips_executor(self, pipeline, tmp_path):
        """When dry_run is True, executor should not be called."""
        service, finder, extractor, resolver, executor = pipeline
        src = Path("/in/photo.jpg")
        dest = Path("/out/2024/01/01/photo.jpg")

        finder.find.return_value = [src]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = dest

        config = make_config(tmp_path, dry_run=True)
        results, _ = service.process(config)

        assert len(results) == 1
        assert results[0].status == "success"
        assert results[0].destination == dest
        executor.execute.assert_not_called()

    def test_dry_run_unknown_status_when_no_date_and_handle_unknown(self, pipeline, tmp_path):
        """When dry_run with no date and handle_unknown=True, status should be unknown."""
        service, finder, extractor, resolver, executor = pipeline
        finder.find.return_value = [Path("/in/photo.jpg")]
        extractor.extract.return_value = {}  # No date
        resolver.resolve.return_value = Path("/out/.unknown/photo.jpg")

        config = make_config(tmp_path, dry_run=True, handle_unknown=True)
        results, _ = service.process(config)

        assert results[0].status == "unknown"
        assert results[0].destination == Path("/out/.unknown/photo.jpg")
        executor.execute.assert_not_called()

    def test_dry_run_success_when_no_date_and_no_handle_unknown(self, pipeline, tmp_path):
        """When dry_run with no date and handle_unknown=False, status should be success if dest exists."""
        service, finder, extractor, resolver, executor = pipeline
        finder.find.return_value = [Path("/in/photo.jpg")]
        extractor.extract.return_value = {}  # No date
        resolver.resolve.return_value = Path("/out/photo.jpg")

        config = make_config(tmp_path, dry_run=True, handle_unknown=False)
        results, _ = service.process(config)

        # With no date and handle_unknown=False, but dest is resolved, status is success
        assert results[0].status == "success"
        executor.execute.assert_not_called()

    def test_dry_run_skips_when_dest_exists_on_disk(self, pipeline, tmp_path):
        """Dry run should mark as skipped if destination file already exists."""
        service, finder, extractor, resolver, executor = pipeline

        # Create actual destination file
        out_dir = tmp_path / "output" / "2024" / "01"
        out_dir.mkdir(parents=True)
        existing_dest = out_dir / "photo.jpg"
        existing_dest.write_text("existing")

        finder.find.return_value = [Path("/in/photo.jpg")]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = existing_dest

        config = make_config(tmp_path, dry_run=True)
        results, _ = service.process(config)

        assert results[0].status == "skipped"
        executor.execute.assert_not_called()

    def test_dry_run_skips_duplicate_destinations(self, pipeline, tmp_path):
        """Dry run should mark as skipped if two files resolve to same destination."""
        service, finder, extractor, resolver, executor = pipeline
        dest = Path("/out/2024/01/01/photo.jpg")

        finder.find.return_value = [Path("/in/photo1.jpg"), Path("/in/photo2.jpg")]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = dest  # Both resolve to same destination

        config = make_config(tmp_path, dry_run=True)
        results, _ = service.process(config)

        assert len(results) == 2
        assert results[0].status == "success"
        assert results[0].destination == dest
        assert results[1].status == "skipped"  # Second file skipped - dest claimed
        executor.execute.assert_not_called()


class TestProcessingServiceCancelEvent:
    def test_cancel_event_stops_processing(self, pipeline, tmp_path):
        """When cancel_event is set, processing should stop."""
        service, finder, extractor, resolver, _ = pipeline
        finder.find.return_value = [Path(f"/in/photo{i}.jpg") for i in range(10)]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = Path("/out/photo.jpg")

        cancel_event = threading.Event()
        processed = []

        def on_progress(result):
            processed.append(result)
            if len(processed) >= 3:
                cancel_event.set()

        config = make_config(tmp_path)
        results, stats = service.process(config, on_progress=on_progress, cancel_event=cancel_event)

        # Should have stopped after 3 files
        assert len(results) == 3
        assert stats.file_count == 3

    def test_cancel_event_not_set_processes_all(self, pipeline, tmp_path):
        """When cancel_event is provided but not set, all files should be processed."""
        service, finder, extractor, resolver, _ = pipeline
        finder.find.return_value = [Path(f"/in/photo{i}.jpg") for i in range(5)]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = Path("/out/photo.jpg")

        cancel_event = threading.Event()
        config = make_config(tmp_path)
        results, _ = service.process(config, cancel_event=cancel_event)

        assert len(results) == 5

    def test_cancel_event_none_processes_all(self, pipeline, tmp_path):
        """When cancel_event is None, all files should be processed."""
        service, finder, extractor, resolver, _ = pipeline
        finder.find.return_value = [Path(f"/in/photo{i}.jpg") for i in range(5)]
        extractor.extract.return_value = {"date": datetime(2024, 1, 1)}
        resolver.resolve.return_value = Path("/out/photo.jpg")

        config = make_config(tmp_path)
        results, _ = service.process(config, cancel_event=None)

        assert len(results) == 5
