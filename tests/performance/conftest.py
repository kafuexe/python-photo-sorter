"""Shared fixtures for performance tests."""
import io
from pathlib import Path

import pytest
from PIL import Image
from PIL.ExifTags import Base as ExifBase


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )


@pytest.fixture
def perf_tmp_dir(tmp_path):
    """Temporary directory for performance test files."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    return input_dir, output_dir


def _create_minimal_jpeg(path: Path, exif_date: str | None = None) -> Path:
    """Create a minimal JPEG file, optionally with EXIF date."""
    img = Image.new("RGB", (10, 10), color="red")

    exif_bytes = None
    if exif_date:
        exif = img.getexif()
        exif[ExifBase.DateTimeOriginal] = exif_date

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", exif=exif)
        path.write_bytes(buffer.getvalue())
    else:
        img.save(path, format="JPEG")

    return path


@pytest.fixture
def generate_exif_files(perf_tmp_dir):
    """Generate test files with EXIF data."""
    input_dir, _ = perf_tmp_dir

    def _generate(count: int) -> list[Path]:
        files = []
        for i in range(count):
            month = (i % 12) + 1
            day = (i % 28) + 1
            path = input_dir / f"photo_{i:04d}.jpg"
            _create_minimal_jpeg(path, f"2024:{month:02d}:{day:02d} 12:00:00")
            files.append(path)
        return files

    return _generate


@pytest.fixture
def generate_filename_files(perf_tmp_dir):
    """Generate test files with handler-specific filename patterns (no EXIF)."""
    input_dir, _ = perf_tmp_dir

    patterns = {
        "samsung": lambda i: f"2024{(i%12)+1:02d}{(i%28)+1:02d}_{12:02d}{i%60:02d}{i%60:02d}.jpg",
        "pixel": lambda i: f"PXL_2024{(i%12)+1:02d}{(i%28)+1:02d}_{12:02d}{i%60:02d}{i%60:02d}.jpg",
        "telegram": lambda i: f"photo_2024-{(i%12)+1:02d}-{(i%28)+1:02d}_{12:02d}-{i%60:02d}-{i%60:02d}.jpg",
        "screenshot": lambda i: f"Screenshot_2024{(i%12)+1:02d}{(i%28)+1:02d}-{12:02d}{i%60:02d}{i%60:02d}.png",
        "datestamp": lambda i: f"2024-{(i%12)+1:02d}-{(i%28)+1:02d} 12.{i%60:02d}.{i%60:02d}.jpg",
        "whatsapp": lambda i: f"IMG-2024{(i%12)+1:02d}{(i%28)+1:02d}-WA{i:04d}.jpg",
    }

    def _generate(count: int, pattern: str = "samsung") -> list[Path]:
        name_fn = patterns.get(pattern, patterns["samsung"])
        files = []
        for i in range(count):
            path = input_dir / name_fn(i)
            _create_minimal_jpeg(path)
            files.append(path)
        return files

    return _generate


@pytest.fixture
def generate_mixed_files(perf_tmp_dir):
    """Generate a mix of EXIF and filename-based files."""
    input_dir, _ = perf_tmp_dir

    def _generate(count: int) -> list[Path]:
        files = []
        for i in range(count):
            month = (i % 12) + 1
            day = (i % 28) + 1

            if i % 3 == 0:
                # EXIF file
                path = input_dir / f"photo_{i:04d}.jpg"
                _create_minimal_jpeg(path, f"2024:{month:02d}:{day:02d} 12:00:00")
            elif i % 3 == 1:
                # Samsung pattern
                path = input_dir / f"2024{month:02d}{day:02d}_{12:02d}{i%60:02d}{i%60:02d}.jpg"
                _create_minimal_jpeg(path)
            else:
                # WhatsApp pattern
                path = input_dir / f"IMG-2024{month:02d}{day:02d}-WA{i:04d}.jpg"
                _create_minimal_jpeg(path)

            files.append(path)
        return files

    return _generate
