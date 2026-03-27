"""Performance tests for the end-to-end processing pipeline."""
import pytest

from src.handlers.registry import HandlerRegistry
from src.handlers.pillow_exif_handler import PillowExifHandler
from src.handlers.exifread_handler import ExifReadHandler
from src.handlers.whatsapp_handler import WhatsAppHandler
from src.handlers.samsung_handler import SamsungHandler
from src.handlers.pixel_handler import PixelHandler
from src.handlers.telegram_handler import TelegramHandler
from src.handlers.screenshot_handler import ScreenshotHandler
from src.handlers.datestamp_handler import DatestampHandler
from src.services.processing_service import ProcessingService
from src.models.processing_config import ProcessingConfig
from src.steps import FileFinder, MetadataExtractor, DestinationResolver, FileExecutor


@pytest.fixture
def full_registry():
    """Registry with all handlers registered."""
    registry = HandlerRegistry()
    registry.register(PillowExifHandler())
    registry.register(ExifReadHandler())
    registry.register(WhatsAppHandler())
    registry.register(SamsungHandler())
    registry.register(PixelHandler())
    registry.register(TelegramHandler())
    registry.register(ScreenshotHandler())
    registry.register(DatestampHandler())
    return registry


@pytest.fixture
def pipeline_service(full_registry):
    """Full processing pipeline service."""
    return ProcessingService(
        file_finder=FileFinder(),
        metadata_extractor=MetadataExtractor(full_registry),
        destination_resolver=DestinationResolver(),
        file_executor=FileExecutor(),
    )


def make_config(input_dir, output_dir, **overrides):
    """Create a processing config."""
    defaults = {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "date_format": "%Y/%m/%d",
        "action": "copy",
        "selected_extensions": ["jpg", "jpeg", "png"],
        "handle_unknown": True,
    }
    defaults.update(overrides)
    return ProcessingConfig(**defaults)


# =====================
# Pipeline Throughput
# =====================

@pytest.mark.benchmark(group="pipeline-throughput")
class TestPipelineThroughput:
    """Test overall pipeline throughput."""

    def test_pipeline_10_exif_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_exif_files):
        """Pipeline throughput with 10 EXIF files."""
        input_dir, output_dir = perf_tmp_dir
        generate_exif_files(10)
        config = make_config(input_dir, output_dir)

        def run():
            # Clear output for each iteration
            for f in output_dir.iterdir():
                if f.is_file():
                    f.unlink()
            return pipeline_service.process(config)

        results, stats = benchmark.pedantic(run, iterations=1, rounds=5)
        assert stats.file_count == 10

    def test_pipeline_50_exif_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_exif_files):
        """Pipeline throughput with 50 EXIF files."""
        input_dir, output_dir = perf_tmp_dir
        generate_exif_files(50)
        config = make_config(input_dir, output_dir)

        def run():
            for f in output_dir.iterdir():
                if f.is_file():
                    f.unlink()
            return pipeline_service.process(config)

        results, stats = benchmark.pedantic(run, iterations=1, rounds=3)
        assert stats.file_count == 50

    def test_pipeline_50_filename_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_filename_files):
        """Pipeline throughput with 50 filename-pattern files."""
        input_dir, output_dir = perf_tmp_dir
        generate_filename_files(50, "samsung")
        config = make_config(input_dir, output_dir)

        def run():
            for f in output_dir.iterdir():
                if f.is_file():
                    f.unlink()
            return pipeline_service.process(config)

        results, stats = benchmark.pedantic(run, iterations=1, rounds=3)
        assert stats.file_count == 50

    def test_pipeline_100_mixed_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_mixed_files):
        """Pipeline throughput with 100 mixed files."""
        input_dir, output_dir = perf_tmp_dir
        generate_mixed_files(100)
        config = make_config(input_dir, output_dir)

        def run():
            for f in output_dir.iterdir():
                if f.is_file():
                    f.unlink()
            return pipeline_service.process(config)

        results, stats = benchmark.pedantic(run, iterations=1, rounds=3)
        assert stats.file_count == 100


# =====================
# Dry Run Performance
# =====================

@pytest.mark.benchmark(group="dry-run")
class TestDryRunPerformance:
    """Test dry run mode performance (no file I/O)."""

    def test_dry_run_50_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_mixed_files):
        """Dry run with 50 files."""
        input_dir, output_dir = perf_tmp_dir
        generate_mixed_files(50)
        config = make_config(input_dir, output_dir, dry_run=True)

        results, stats = benchmark(lambda: pipeline_service.process(config))
        assert stats.file_count == 50

    def test_dry_run_100_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_mixed_files):
        """Dry run with 100 files."""
        input_dir, output_dir = perf_tmp_dir
        generate_mixed_files(100)
        config = make_config(input_dir, output_dir, dry_run=True)

        results, stats = benchmark(lambda: pipeline_service.process(config))
        assert stats.file_count == 100

    def test_dry_run_200_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_mixed_files):
        """Dry run with 200 files."""
        input_dir, output_dir = perf_tmp_dir
        generate_mixed_files(200)
        config = make_config(input_dir, output_dir, dry_run=True)

        results, stats = benchmark(lambda: pipeline_service.process(config))
        assert stats.file_count == 200


# =====================
# Pipeline Steps
# =====================

@pytest.mark.benchmark(group="pipeline-steps")
class TestPipelineSteps:
    """Benchmark individual pipeline steps."""

    def test_file_finder(self, benchmark, perf_tmp_dir, generate_mixed_files):
        """Benchmark file discovery step."""
        input_dir, _ = perf_tmp_dir
        generate_mixed_files(100)
        finder = FileFinder()

        files = benchmark(lambda: finder.find(input_dir, ["jpg", "jpeg", "png"]))
        assert len(files) == 100

    def test_metadata_extractor(self, benchmark, full_registry, perf_tmp_dir, generate_mixed_files):
        """Benchmark metadata extraction step."""
        input_dir, _ = perf_tmp_dir
        files = generate_mixed_files(50)
        extractor = MetadataExtractor(full_registry)

        results = benchmark(lambda: [extractor.extract(f) for f in files])
        assert len(results) == 50

    def test_destination_resolver(self, benchmark, perf_tmp_dir, generate_mixed_files):
        """Benchmark destination resolution step."""
        input_dir, output_dir = perf_tmp_dir
        files = generate_mixed_files(50)
        resolver = DestinationResolver()
        config = make_config(input_dir, output_dir)

        # Pre-extract metadata
        from datetime import datetime
        metadata = {"date": datetime(2024, 6, 15)}

        results = benchmark(lambda: [resolver.resolve(f, metadata, config) for f in files])
        assert len(results) == 50


# =====================
# Scaling Tests
# =====================

@pytest.mark.benchmark(group="scaling")
class TestPipelineScaling:
    """Test how pipeline performance scales."""

    def test_scale_25_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_mixed_files):
        """Baseline: 25 files."""
        input_dir, output_dir = perf_tmp_dir
        generate_mixed_files(25)
        config = make_config(input_dir, output_dir, dry_run=True)

        benchmark(lambda: pipeline_service.process(config))

    def test_scale_50_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_mixed_files):
        """Scale: 50 files."""
        input_dir, output_dir = perf_tmp_dir
        generate_mixed_files(50)
        config = make_config(input_dir, output_dir, dry_run=True)

        benchmark(lambda: pipeline_service.process(config))

    def test_scale_100_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_mixed_files):
        """Scale: 100 files."""
        input_dir, output_dir = perf_tmp_dir
        generate_mixed_files(100)
        config = make_config(input_dir, output_dir, dry_run=True)

        benchmark(lambda: pipeline_service.process(config))

    def test_scale_200_files(self, benchmark, pipeline_service, perf_tmp_dir, generate_mixed_files):
        """Scale: 200 files."""
        input_dir, output_dir = perf_tmp_dir
        generate_mixed_files(200)
        config = make_config(input_dir, output_dir, dry_run=True)

        benchmark(lambda: pipeline_service.process(config))
