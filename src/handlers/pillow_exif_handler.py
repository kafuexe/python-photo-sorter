from datetime import datetime
from pathlib import Path

from PIL import Image

from .base import BaseHandler


EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"

EXIF_DATE_TAGS = [
    (36867, 37521),  # (DateTimeOriginal, SubsecTimeOriginal)
    (36868, 37522),  # (DateTimeDigitized, SubsecTimeDigitized)
    (306, 37520),    # (DateTime, SubsecTime)
]


class PillowExifHandler(BaseHandler):
    def supported_extensions(self) -> list[str]:
        return ["jpg", "jpeg", "png", "webp"]

    def priority(self) -> int:
        return 10

    def extract_metadata(self, file_path: Path) -> dict:
        try:
            exif = Image.open(file_path).getexif()
        except Exception:
            return {}

        metadata = {}

        for date_tag, subsec_tag in EXIF_DATE_TAGS:
            dat = exif.get(date_tag)
            sub = exif.get(subsec_tag, 0)

            dat = dat[0] if isinstance(dat, tuple) else dat
            sub = sub[0] if isinstance(sub, tuple) else sub

            if dat and str(dat).strip():
                try:
                    date_str = str(dat).strip()[:19]
                    metadata["date"] = datetime.strptime(date_str, EXIF_DATE_FORMAT)
                    if sub:
                        metadata["subsecond"] = str(sub)
                    break
                except ValueError:
                    continue

        return metadata
