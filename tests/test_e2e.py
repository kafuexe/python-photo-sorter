"""End-to-end tests for the full processing pipeline with real files."""
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.ExifTags import Base as ExifBase

from src.handlers.registry import HandlerRegistry
from src.handlers.pillow_exif_handler import PillowExifHandler
from src.services.config_service import ConfigService
from src.services.processing_service import ProcessingService
from src.steps import FileFinder, MetadataExtractor, DestinationResolver, FileExecutor
from src.models.processing_config import ProcessingConfig


def _make_pipeline():
    registry = HandlerRegistry()
    registry.register(PillowExifHandler())

    return ProcessingService(
        file_finder=FileFinder(),
        metadata_extractor=MetadataExtractor(registry),
        destination_resolver=DestinationResolver(),
        file_executor=FileExecutor(),
    ), registry


def _create_image_with_exif(path: Path, date_str: str):
    img = Image.new("RGB", (10, 10))
    exif = img.getexif()
    exif[ExifBase.DateTimeOriginal] = date_str
    img.save(path, exif=exif)


def _create_image_no_exif(path: Path):
    img = Image.new("RGB", (10, 10))
    img.save(path)


class TestE2ECopyWithExif:
    def test_sorts_by_date(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        _create_image_with_exif(input_dir / "summer.jpg", "2024:06:15 14:30:00")
        _create_image_with_exif(input_dir / "winter.jpg", "2024:12:25 10:00:00")

        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            date_format="%Y/%m/%d",
            action="copy",
            selected_extensions=["jpg"],
            handle_unknown=True,
        )

        results = service.process(config)

        assert len(results) == 2
        assert all(r.status == "success" for r in results)
        assert (output_dir / "2024" / "06" / "15" / "summer.jpg").exists()
        assert (output_dir / "2024" / "12" / "25" / "winter.jpg").exists()
        # originals still exist (copy mode)
        assert (input_dir / "summer.jpg").exists()
        assert (input_dir / "winter.jpg").exists()


class TestE2EMoveWithExif:
    def test_moves_files(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        _create_image_with_exif(input_dir / "photo.jpg", "2023:03:10 08:00:00")

        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            date_format="%Y/%m",
            action="move",
            selected_extensions=["jpg"],
        )

        results = service.process(config)

        assert len(results) == 1
        assert results[0].status == "success"
        assert (output_dir / "2023" / "03" / "photo.jpg").exists()
        assert not (input_dir / "photo.jpg").exists()  # moved


class TestE2ENoExifFallbackToFileStat:
    def test_no_exif_treated_as_unknown(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        _create_image_no_exif(input_dir / "nodate.jpg")

        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            date_format="%Y/%m/%d",
            action="copy",
            selected_extensions=["jpg"],
            handle_unknown=True,
        )

        results = service.process(config)

        assert len(results) == 1
        assert results[0].status == "unknown"
        assert results[0].metadata.get("date") is None
        assert results[0].destination.exists()


class TestE2EUnknownHandling:
    def test_unknown_files_moved_to_unknown_folder(self, tmp_path):
        """When no handler returns a date, files go to the unknown folder."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        (input_dir / "notes.txt").write_text("hello")

        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            date_format="%Y/%m/%d",
            action="copy",
            selected_extensions=["txt"],
            handle_unknown=True,
            unknown_folder_name=".nodate",
        )

        results = service.process(config)

        assert len(results) == 1
        assert results[0].status == "unknown"
        assert (output_dir / ".nodate" / "notes.txt").exists()

    def test_unknown_files_skipped_when_disabled(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        (input_dir / "notes.txt").write_text("hello")

        registry = HandlerRegistry()
        service = ProcessingService(
            file_finder=FileFinder(),
            metadata_extractor=MetadataExtractor(registry),
            destination_resolver=DestinationResolver(),
            file_executor=FileExecutor(),
        )
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            action="copy",
            selected_extensions=["txt"],
            handle_unknown=False,
        )

        results = service.process(config)

        assert len(results) == 1
        assert results[0].status == "skipped"
        assert not any(output_dir.rglob("*"))


class TestE2EFilenameCollisions:
    def test_duplicate_filenames_skip_second(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        # Two images with same name in different subdirs, same EXIF date
        sub1 = input_dir / "trip1"
        sub2 = input_dir / "trip2"
        sub1.mkdir()
        sub2.mkdir()

        _create_image_with_exif(sub1 / "photo.jpg", "2024:01:01 12:00:00")
        _create_image_with_exif(sub2 / "photo.jpg", "2024:01:01 12:00:00")

        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            date_format="%Y/%m/%d",
            action="copy",
            selected_extensions=["jpg"],
        )

        results = service.process(config)

        assert len(results) == 2
        statuses = [r.status for r in results]
        assert statuses.count("success") == 1
        assert statuses.count("skipped") == 1

        dest_dir = output_dir / "2024" / "01" / "01"
        files = list(dest_dir.iterdir())
        assert len(files) == 1
        assert files[0].name == "photo.jpg"


class TestE2EExtensionFiltering:
    def test_only_selected_extensions_processed(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        _create_image_with_exif(input_dir / "include.jpg", "2024:01:01 12:00:00")
        _create_image_with_exif(input_dir / "exclude.png", "2024:01:01 12:00:00")

        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            date_format="%Y",
            action="copy",
            selected_extensions=["jpg"],  # only jpg
        )

        results = service.process(config)

        assert len(results) == 1
        assert results[0].source.name == "include.jpg"


class TestE2ECustomDateFormat:
    def test_flat_format(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        _create_image_with_exif(input_dir / "photo.jpg", "2024:06:15 14:30:00")

        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            date_format="%Y%m%d",
            action="copy",
            selected_extensions=["jpg"],
        )

        results = service.process(config)

        assert (output_dir / "20240615" / "photo.jpg").exists()

    def test_year_month_format(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        _create_image_with_exif(input_dir / "photo.jpg", "2024:06:15 14:30:00")

        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            date_format="%Y-%m",
            action="copy",
            selected_extensions=["jpg"],
        )

        results = service.process(config)

        assert (output_dir / "2024-06" / "photo.jpg").exists()


class TestE2EProgressCallback:
    def test_callback_called_per_file(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        for i in range(3):
            _create_image_with_exif(input_dir / f"photo{i}.jpg", "2024:01:01 12:00:00")

        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            date_format="%Y",
            action="copy",
            selected_extensions=["jpg"],
        )

        progress = []
        results = service.process(config, on_progress=progress.append)

        assert len(progress) == 3
        assert len(results) == 3
        assert all(r.status == "success" for r in results)


class TestE2EConfigRoundtrip:
    def test_save_and_reload_config(self, tmp_path):
        config_path = tmp_path / "config.json"
        cs = ConfigService(config_path=config_path)

        original = ProcessingConfig(
            input_dir="/photos/input",
            output_dir="/photos/output",
            date_format="%Y-%m-%d",
            action="move",
            selected_extensions=["jpg", "png", "mp4"],
            handle_unknown=False,
            unknown_folder_name=".unrecognized",
        )

        cs.save(original.to_dict())
        loaded = cs.load()
        restored = ProcessingConfig.from_dict(loaded, action="copy")

        assert str(restored.input_dir) == str(original.input_dir)
        assert str(restored.output_dir) == str(original.output_dir)
        assert restored.date_format == original.date_format
        assert restored.selected_extensions == original.selected_extensions
        assert restored.handle_unknown == original.handle_unknown
        assert restored.unknown_folder_name == original.unknown_folder_name


class TestE2EEmptyInput:
    def test_empty_directory(self, tmp_path):
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            action="copy",
            selected_extensions=["jpg"],
        )

        results = service.process(config)
        assert results == []

    def test_nonexistent_input(self, tmp_path):
        service, _ = _make_pipeline()
        config = ProcessingConfig(
            input_dir=tmp_path / "nope",
            output_dir=tmp_path / "output",
            action="copy",
            selected_extensions=["jpg"],
        )

        results = service.process(config)
        assert results == []
