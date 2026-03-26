"""End-to-end tests for the full processing pipeline with real files."""
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image
from PIL.ExifTags import Base as ExifBase

from src.handlers.registry import HandlerRegistry
from src.handlers.pillow_exif_handler import PillowExifHandler
from src.handlers.whatsapp_handler import WhatsAppHandler
from src.services.config_service import ConfigService
from src.services.processing_service import ProcessingService
from src.steps import FileFinder, MetadataExtractor, DestinationResolver, FileExecutor
from src.models.processing_config import ProcessingConfig


@pytest.fixture
def pipeline():
    registry = HandlerRegistry()
    registry.register(PillowExifHandler())

    service = ProcessingService(
        file_finder=FileFinder(),
        metadata_extractor=MetadataExtractor(registry),
        destination_resolver=DestinationResolver(),
        file_executor=FileExecutor(),
    )
    return service, registry


@pytest.fixture
def dirs(tmp_path):
    """Create and return (input_dir, output_dir)."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    return input_dir, output_dir


def create_image_with_exif(path: Path, date_str: str):
    img = Image.new("RGB", (10, 10))
    exif = img.getexif()
    exif[ExifBase.DateTimeOriginal] = date_str
    img.save(path, exif=exif)


def create_image_no_exif(path: Path):
    Image.new("RGB", (10, 10)).save(path)


def make_config(input_dir, output_dir, **overrides):
    defaults = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "date_format": "%Y/%m/%d",
        "action": "copy",
        "selected_extensions": ["jpg"],
        "handle_unknown": True,
    }
    defaults.update(overrides)
    return ProcessingConfig(**defaults)


class TestE2ECopyMove:
    @pytest.mark.parametrize("action, source_survives", [
        ("copy", True),
        ("move", False),
    ])
    def test_transfers_file_by_exif_date(self, pipeline, dirs, action, source_survives):
        service, _ = pipeline
        input_dir, output_dir = dirs

        create_image_with_exif(input_dir / "photo.jpg", "2024:06:15 14:30:00")
        config = make_config(input_dir, output_dir, action=action)

        results, _ = service.process(config)

        assert len(results) == 1
        assert results[0].status == "success"
        assert (output_dir / "2024" / "06" / "15" / "photo.jpg").exists()
        assert (input_dir / "photo.jpg").exists() == source_survives

    def test_sorts_multiple_files_by_date(self, pipeline, dirs):
        service, _ = pipeline
        input_dir, output_dir = dirs

        create_image_with_exif(input_dir / "summer.jpg", "2024:06:15 14:30:00")
        create_image_with_exif(input_dir / "winter.jpg", "2024:12:25 10:00:00")
        config = make_config(input_dir, output_dir)

        results, _ = service.process(config)

        assert len(results) == 2
        assert all(r.status == "success" for r in results)
        assert (output_dir / "2024" / "06" / "15" / "summer.jpg").exists()
        assert (output_dir / "2024" / "12" / "25" / "winter.jpg").exists()


class TestE2EDateFormats:
    @pytest.mark.parametrize("date_format, expected_subpath", [
        ("%Y%m%d",  "20240615"),
        ("%Y-%m",   "2024-06"),
        ("%Y/%m/%d", "2024/06/15"),
    ])
    def test_custom_date_format(self, pipeline, dirs, date_format, expected_subpath):
        service, _ = pipeline
        input_dir, output_dir = dirs

        create_image_with_exif(input_dir / "photo.jpg", "2024:06:15 14:30:00")
        config = make_config(input_dir, output_dir, date_format=date_format)

        results, _ = service.process(config)

        assert (output_dir / expected_subpath / "photo.jpg").exists()


class TestE2EUnknownHandling:
    def test_no_exif_routes_to_unknown_folder(self, pipeline, dirs):
        service, _ = pipeline
        input_dir, output_dir = dirs

        create_image_no_exif(input_dir / "nodate.jpg")
        config = make_config(input_dir, output_dir, handle_unknown=True)

        results, _ = service.process(config)

        assert results[0].status == "unknown"
        assert results[0].metadata.get("date") is None
        assert results[0].destination.exists()

    def test_unknown_files_use_custom_folder_name(self, pipeline, dirs):
        service, _ = pipeline
        input_dir, output_dir = dirs

        (input_dir / "notes.txt").write_text("hello")
        config = make_config(input_dir, output_dir,
                             selected_extensions=["txt"],
                             unknown_folder_name=".nodate")

        results, _ = service.process(config)

        assert results[0].status == "unknown"
        assert (output_dir / ".nodate" / "notes.txt").exists()

    def test_unknown_files_skipped_when_disabled(self, dirs):
        input_dir, output_dir = dirs
        (input_dir / "notes.txt").write_text("hello")

        registry = HandlerRegistry()
        service = ProcessingService(
            file_finder=FileFinder(),
            metadata_extractor=MetadataExtractor(registry),
            destination_resolver=DestinationResolver(),
            file_executor=FileExecutor(),
        )
        config = make_config(input_dir, output_dir,
                             selected_extensions=["txt"],
                             handle_unknown=False)

        results, _ = service.process(config)

        assert results[0].status == "skipped"
        assert not any(output_dir.rglob("*"))


class TestE2ECollisions:
    def test_duplicate_filenames_skip_second(self, pipeline, dirs):
        service, _ = pipeline
        input_dir, output_dir = dirs

        sub1 = input_dir / "trip1"
        sub2 = input_dir / "trip2"
        sub1.mkdir()
        sub2.mkdir()

        create_image_with_exif(sub1 / "photo.jpg", "2024:01:01 12:00:00")
        create_image_with_exif(sub2 / "photo.jpg", "2024:01:01 12:00:00")

        config = make_config(input_dir, output_dir)
        results, _ = service.process(config)

        statuses = [r.status for r in results]
        assert statuses.count("success") == 1
        assert statuses.count("skipped") == 1

        dest_files = list((output_dir / "2024" / "01" / "01").iterdir())
        assert len(dest_files) == 1


class TestE2EExtensionFiltering:
    def test_only_selected_extensions_processed(self, pipeline, dirs):
        service, _ = pipeline
        input_dir, output_dir = dirs

        create_image_with_exif(input_dir / "include.jpg", "2024:01:01 12:00:00")
        create_image_with_exif(input_dir / "exclude.png", "2024:01:01 12:00:00")

        config = make_config(input_dir, output_dir, selected_extensions=["jpg"])
        results, _ = service.process(config)

        assert len(results) == 1
        assert results[0].source.name == "include.jpg"


class TestE2EProgressCallback:
    def test_callback_called_per_file(self, pipeline, dirs):
        service, _ = pipeline
        input_dir, output_dir = dirs

        for i in range(3):
            create_image_with_exif(input_dir / f"photo{i}.jpg", "2024:01:01 12:00:00")

        config = make_config(input_dir, output_dir, date_format="%Y")
        progress = []
        results, _ = service.process(config, on_progress=progress.append)

        assert len(progress) == 3
        assert all(r.status == "success" for r in results)


class TestE2EConfigRoundtrip:
    def test_save_and_reload_config(self, tmp_path):
        cs = ConfigService(config_path=tmp_path / "config.json")

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
        restored = ProcessingConfig.from_dict(cs.load(), action="copy")

        for attr in ("date_format", "selected_extensions", "handle_unknown", "unknown_folder_name"):
            assert getattr(restored, attr) == getattr(original, attr)


class TestE2EEmptyInput:
    @pytest.mark.parametrize("input_exists", [True, False])
    def test_empty_or_missing_input_returns_empty(self, pipeline, tmp_path, input_exists):
        service, _ = pipeline
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        if input_exists:
            input_dir.mkdir()
        output_dir.mkdir()

        config = make_config(input_dir, output_dir)
        results, _ = service.process(config)
        assert results == []


class TestE2EWhatsApp:
    @pytest.fixture
    def whatsapp_pipeline(self):
        registry = HandlerRegistry()
        registry.register(PillowExifHandler())
        registry.register(WhatsAppHandler())

        service = ProcessingService(
            file_finder=FileFinder(),
            metadata_extractor=MetadataExtractor(registry),
            destination_resolver=DestinationResolver(),
            file_executor=FileExecutor(),
        )
        return service

    def test_whatsapp_image_sorted_by_filename_date(self, whatsapp_pipeline, dirs):
        input_dir, output_dir = dirs
        # WhatsApp images lack EXIF — date comes from filename
        (input_dir / "IMG-20230415-WA0012.jpg").write_bytes(b"fake jpg")

        config = make_config(input_dir, output_dir, date_format="%Y/%m/%d")
        results, _ = whatsapp_pipeline.process(config)

        assert len(results) == 1
        assert results[0].status == "success"
        assert (output_dir / "2023" / "04" / "15" / "IMG-20230415-WA0012.jpg").exists()

    def test_whatsapp_video_sorted_by_filename_date(self, whatsapp_pipeline, dirs):
        input_dir, output_dir = dirs
        (input_dir / "VID-20220801-WA0003.mp4").write_bytes(b"fake mp4")

        config = make_config(input_dir, output_dir,
                             selected_extensions=["mp4"], date_format="%Y/%m")
        results, _ = whatsapp_pipeline.process(config)

        assert len(results) == 1
        assert results[0].status == "success"
        assert (output_dir / "2022" / "08" / "VID-20220801-WA0003.mp4").exists()

    def test_whatsapp_handler_wins_when_no_exif(self, whatsapp_pipeline, dirs):
        """For a WhatsApp-named file without EXIF, the filename date should be used."""
        input_dir, output_dir = dirs
        create_image_no_exif(input_dir / "IMG-20210601-WA0001.jpg")

        config = make_config(input_dir, output_dir)
        results, _ = whatsapp_pipeline.process(config)

        assert results[0].status == "success"
        assert results[0].metadata["date"] == datetime(2021, 6, 1)

    def test_non_whatsapp_file_still_goes_to_unknown(self, whatsapp_pipeline, dirs):
        input_dir, output_dir = dirs
        # A regular file without EXIF and without WhatsApp naming
        create_image_no_exif(input_dir / "random_photo.jpg")

        config = make_config(input_dir, output_dir, handle_unknown=True)
        results, _ = whatsapp_pipeline.process(config)

        assert results[0].status == "unknown"


class TestE2EHandlerPriority:
    def test_exif_date_takes_precedence_over_whatsapp_filename(self, dirs):
        """When EXIF is present, its date should win over the filename date."""
        input_dir, output_dir = dirs

        registry = HandlerRegistry()
        registry.register(PillowExifHandler())   # priority 10
        registry.register(WhatsAppHandler())     # priority 10

        service = ProcessingService(
            file_finder=FileFinder(),
            metadata_extractor=MetadataExtractor(registry),
            destination_resolver=DestinationResolver(),
            file_executor=FileExecutor(),
        )

        # File named as WhatsApp (2023-04-15) but EXIF says 2024-06-15
        create_image_with_exif(input_dir / "IMG-20230415-WA0012.jpg", "2024:06:15 14:30:00")
        config = make_config(input_dir, output_dir)
        results, _ = service.process(config)

        # Pillow runs first (registered first, same priority), so EXIF date wins
        assert results[0].metadata["date"] == datetime(2024, 6, 15, 14, 30)
