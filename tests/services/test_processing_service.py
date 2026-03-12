from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

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


class TestProcessingService:
    def _make_service(self, files=None, metadata=None, dest=None):
        finder = MagicMock()
        finder.find.return_value = files or []

        extractor = MagicMock()
        extractor.extract.return_value = metadata or {}

        resolver = MagicMock()
        resolver.resolve.return_value = dest

        executor = MagicMock()

        service = ProcessingService(
            file_finder=finder,
            metadata_extractor=extractor,
            destination_resolver=resolver,
            file_executor=executor,
        )
        return service, finder, extractor, resolver, executor

    def test_empty_directory(self, tmp_path):
        service, finder, _, _, _ = self._make_service(files=[])
        config = make_config(tmp_path)

        results = service.process(config)
        assert results == []
        finder.find.assert_called_once()

    def test_successful_processing(self, tmp_path):
        src = Path("/in/photo.jpg")
        dest = Path("/out/2024/01/01/photo.jpg")
        dt = datetime(2024, 1, 1)

        service, _, extractor, resolver, executor = self._make_service(
            files=[src],
            metadata={"date": dt},
            dest=dest,
        )
        config = make_config(tmp_path)

        results = service.process(config)
        assert len(results) == 1
        assert results[0].status == "success"
        assert results[0].destination == dest
        executor.execute.assert_called_once_with(src, dest, "copy")

    def test_skipped_when_no_dest(self, tmp_path):
        service, _, _, resolver, executor = self._make_service(
            files=[Path("/in/photo.jpg")],
            metadata={},
            dest=None,
        )
        config = make_config(tmp_path, handle_unknown=False)

        results = service.process(config)
        assert len(results) == 1
        assert results[0].status == "skipped"
        executor.execute.assert_not_called()

    def test_unknown_status_when_no_date_but_handled(self, tmp_path):
        dest = Path("/out/.unknown/photo.jpg")
        service, _, _, _, executor = self._make_service(
            files=[Path("/in/photo.jpg")],
            metadata={},
            dest=dest,
        )
        config = make_config(tmp_path, handle_unknown=True)

        results = service.process(config)
        assert len(results) == 1
        assert results[0].status == "unknown"
        executor.execute.assert_called_once()

    def test_error_handling(self, tmp_path):
        service, _, _, _, executor = self._make_service(
            files=[Path("/in/photo.jpg")],
            metadata={"date": datetime(2024, 1, 1)},
            dest=Path("/out/photo.jpg"),
        )
        executor.execute.side_effect = OSError("disk full")
        config = make_config(tmp_path)

        results = service.process(config)
        assert len(results) == 1
        assert results[0].status == "error"
        assert "disk full" in results[0].error

    def test_progress_callback(self, tmp_path):
        service, _, _, _, _ = self._make_service(
            files=[Path("/in/a.jpg"), Path("/in/b.jpg")],
            metadata={"date": datetime(2024, 1, 1)},
            dest=Path("/out/photo.jpg"),
        )
        config = make_config(tmp_path)

        progress_calls = []
        results = service.process(config, on_progress=progress_calls.append)
        assert len(progress_calls) == 2
        assert len(results) == 2

    def test_multiple_files(self, tmp_path):
        files = [Path(f"/in/photo{i}.jpg") for i in range(5)]
        service, _, _, _, _ = self._make_service(
            files=files,
            metadata={"date": datetime(2024, 1, 1)},
            dest=Path("/out/photo.jpg"),
        )
        config = make_config(tmp_path)

        results = service.process(config)
        assert len(results) == 5
