"""Metadata reading functionality for image and video files."""
from datetime import datetime
from pathlib import Path
import os
from PIL import Image


DEFAULT_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"


def get_exif_date(image_path: str) -> str | None:
    """Extract date from image EXIF data.

    Args:
        image_path: Path to the image file.

    Returns:
        Date string in format "YYYY:MM:DD HH:MM:SS" or None if not found.
    """
    try:
        exif = Image.open(image_path).getexif()

        # Try various DateTime tags
        tags = [
            (36867, 37521),  # (DateTimeOriginal, SubsecTimeOriginal)
            (36868, 37522),  # (DateTimeDigitized, SubsecTimeDigitized)
            (306, 37520),     # (DateTime, SubsecTime)
        ]

        for t in tags:
            dat = exif.get(t[0])
            sub = exif.get(t[1], 0)

            # Handle tuple returns from PIL
            dat = dat[0] if isinstance(dat, tuple) else dat
            sub = sub[0] if isinstance(sub, tuple) else sub

            if dat and str(dat).strip():
                # Combine date and subsecond if available
                sub_str = f".{sub}" if sub else ""
                full = f"{dat}{sub_str}"
                return full

    except Exception:
        pass

    return None


def get_video_date(video_path: str, exiftool_path: str | None = None) -> str | None:
    """Extract date from video file using ExifTool.

    Args:
        video_path: Path to the video file.
        exiftool_path: Path to exiftool.exe. Defaults to bundled location.

    Returns:
        Date string or None if not found.
    """
    if not Path(video_path).exists():
        return None

    # Determine exiftool path
    if exiftool_path is None:
        app_dir = Path(__file__).parent.parent.parent
        exiftool_path = app_dir / "exiftool" / "exiftool64.exe"
    else:
        exiftool_path = Path(exiftool_path)

    # Check if exiftool exists
    if not exiftool_path.exists():
        # Try without the 64 suffix
        alt_path = Path(exiftool_path).parent / "exiftool.exe"
        if alt_path.exists():
            exiftool_path = alt_path
        else:
            return None

    try:
        # Run exiftool
        result = os.popen(f'{exiftool_path}" "{video_path}"').read()

        # Find the Create Date line
        for line in result.split("\n"):
            if "Create Date" in line:
                # Extract the date value (after the colon)
                date_str = line.split(":")[1].strip()
                return date_str

    except Exception:
        pass

    return None


def get_file_date(file_path: str) -> str | None:
    """Get date from any supported file type.

    Args:
        file_path: Path to the file.

    Returns:
        Date string or None.
    """
    file_ext = Path(file_path).suffix.lower()

    if file_ext in [".jpg", ".jpeg", ".webp", ".png"]:
        return get_exif_date(file_path)
    elif file_ext in [".mp4", ".mov", ".avi"]:
        return get_video_date(file_path)

    return None


def get_matching_files(directory: str, extensions: list[str]) -> list[str]:
    """Get list of files with matching extensions in directory.

    Args:
        directory: Directory to search.
        extensions: List of file extensions (without dot).

    Returns:
        List of matching file paths.
    """
    if not Path(directory).exists():
        return []

    matching = []
    for file_path in Path(directory).iterdir():
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in extensions:
                matching.append(str(file_path))

    return matching
