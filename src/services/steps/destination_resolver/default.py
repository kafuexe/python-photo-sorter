from pathlib import Path

from ....models.processing_config import ProcessingConfig
from .base import BaseDestinationResolver


class DestinationResolver(BaseDestinationResolver):
    def resolve(self, file_path: Path, metadata: dict,
                config: ProcessingConfig) -> Path | None:
        """Build destination path from metadata date + format string.
        Returns None if no date found and handle_unknown is False.
        Returns path in unknown_folder if no date and handle_unknown is True."""
        date = metadata.get("date")

        if date is not None:
            folder_name = date.strftime(config.date_format)
            return config.output_dir / folder_name / file_path.name

        if config.handle_unknown:
            return config.output_dir / config.unknown_folder_name / file_path.name

        return None
