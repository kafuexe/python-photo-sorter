"""Performance tests for individual metadata extraction handlers."""
import pytest

from src.handlers.samsung_handler import SamsungHandler
from src.handlers.pixel_handler import PixelHandler
from src.handlers.telegram_handler import TelegramHandler
from src.handlers.screenshot_handler import ScreenshotHandler
from src.handlers.datestamp_handler import DatestampHandler
from src.handlers.whatsapp_handler import WhatsAppHandler
from src.handlers.pillow_exif_handler import PillowExifHandler
from src.handlers.exifread_handler import ExifReadHandler


# =====================
# Filename-based Handlers
# =====================

@pytest.mark.benchmark(group="filename-handlers")
class TestFilenameHandlerPerformance:
    """Performance tests for filename-pattern handlers."""

    @pytest.mark.parametrize("handler_cls,pattern", [
        (SamsungHandler, "samsung"),
        (PixelHandler, "pixel"),
        (TelegramHandler, "telegram"),
        (ScreenshotHandler, "screenshot"),
        (DatestampHandler, "datestamp"),
        (WhatsAppHandler, "whatsapp"),
    ])
    def test_handler_throughput(self, benchmark, handler_cls, pattern, generate_filename_files):
        """Measure handler throughput for filename-based extraction."""
        handler = handler_cls()
        files = generate_filename_files(100, pattern)

        def extract_all():
            return [handler.extract_metadata(f) for f in files]

        results = benchmark(extract_all)
        assert len(results) == 100

    @pytest.mark.parametrize("handler_cls,pattern", [
        (SamsungHandler, "samsung"),
        (WhatsAppHandler, "whatsapp"),
    ])
    def test_single_file_extraction(self, benchmark, handler_cls, pattern, generate_filename_files):
        """Benchmark single file extraction."""
        handler = handler_cls()
        files = generate_filename_files(1, pattern)
        file = files[0]

        result = benchmark(lambda: handler.extract_metadata(file))
        assert "date" in result


# =====================
# EXIF-based Handlers
# =====================

@pytest.mark.benchmark(group="exif-handlers")
class TestExifHandlerPerformance:
    """Performance tests for EXIF extraction handlers."""

    @pytest.mark.parametrize("handler_cls", [
        PillowExifHandler,
        ExifReadHandler,
    ])
    def test_exif_handler_throughput(self, benchmark, handler_cls, generate_exif_files):
        """Measure EXIF handler throughput."""
        handler = handler_cls()
        files = generate_exif_files(50)

        def extract_all():
            return [handler.extract_metadata(f) for f in files]

        results = benchmark(extract_all)
        assert len(results) == 50

    def test_pillow_single_file(self, benchmark, generate_exif_files):
        """Benchmark Pillow handler single file extraction."""
        handler = PillowExifHandler()
        files = generate_exif_files(1)
        file = files[0]

        result = benchmark(lambda: handler.extract_metadata(file))
        assert "date" in result

    def test_exifread_single_file(self, benchmark, generate_exif_files):
        """Benchmark ExifRead handler single file extraction."""
        handler = ExifReadHandler()
        files = generate_exif_files(1)
        file = files[0]

        # ExifRead may not extract date from minimal test images
        benchmark(lambda: handler.extract_metadata(file))


# =====================
# Handler Comparison
# =====================

@pytest.mark.benchmark(group="handler-comparison")
class TestHandlerComparison:
    """Compare performance across handlers."""

    def test_samsung_handler(self, benchmark, generate_filename_files):
        handler = SamsungHandler()
        files = generate_filename_files(100, "samsung")
        benchmark(lambda: [handler.extract_metadata(f) for f in files])

    def test_whatsapp_handler(self, benchmark, generate_filename_files):
        handler = WhatsAppHandler()
        files = generate_filename_files(100, "whatsapp")
        benchmark(lambda: [handler.extract_metadata(f) for f in files])

    def test_pillow_exif_handler(self, benchmark, generate_exif_files):
        handler = PillowExifHandler()
        files = generate_exif_files(50)
        benchmark(lambda: [handler.extract_metadata(f) for f in files])

    def test_exifread_handler(self, benchmark, generate_exif_files):
        handler = ExifReadHandler()
        files = generate_exif_files(50)
        benchmark(lambda: [handler.extract_metadata(f) for f in files])
