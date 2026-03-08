"""Core functionality for reading image metadata.

This module provides functions for extracting date/time information
from image files using either PIL or ExifTool.
"""
from datetime import datetime
from pathlib import Path
import os
from PIL import Image


EXIFTOOL_DATE_TAG_VIDEOS = "Create Date"
DEFAULT_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"


class MetaDataReader:
    """Reads metadata from image and video files.

    This class handles extracting date/time information from:
    - JPEG, PNG, WebP images using PIL EXIF data
    - Video files (MP4, MOV, AVI) using ExifTool
    """

    def __init__(self, supported_file_types: list[str]):
        """Initialize the metadata reader.

        Args:
            supported_file_types: List of file extensions to support.
        """
        self.supported_file_types = [ext.lower() for ext in supported_file_types]

    def get_exif_date(self, image_path: str) -> str | None:
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

    def get_video_date(self, video_path: str, exiftool_path: str | None = None) -> str | None:
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
                if EXIFTOOL_DATE_VIDEOS in line:
                    # Extract the date value (after the colon)
                    date_str = line.split(":")[1].strip()
                    return date_str

        except Exception:
            pass

        return None

    def process_file(self, file_path: str) -> str | None:
        """Process a single file and extract its date.

        Args:
            file_path: Path to the file to process.

        Returns:
            Date string or None.
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext in [".jpg", ".jpeg", ".we", ".png"]:
            return self.get_exif_date(file_path)
        elif file_ext in [".mp4", ".mov", ".avi"]:
            return self.get_video_date(file_path)

        return None
