import json
import logging
from pathlib import Path

from ..errors.exceptions import ConfigError

logger = logging.getLogger(__name__)

DEFAULTS = {
    "input_dir": "",
    "output_dir": "",
    "date_format": "%Y/%m/%d",
    "selected_extensions": ["jpg", "png", "webp", "mov", "avi", "mp4"],
    "handle_unknown": True,
    "unknown_folder_name": ".unknown",
}


class ConfigService:
    def __init__(self, config_path: Path | None = None):
        if config_path is None:
            config_path = Path(__file__).resolve().parents[2] / "config.json"
        self._config_path = config_path

    def load(self) -> dict:
        if not self._config_path.exists():
            return self.get_defaults()

        try:
            with open(self._config_path, "r") as f:
                data = json.load(f)
            merged = {**self.get_defaults(), **data}
            return merged
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load config: %s. Using defaults.", e)
            return self.get_defaults()

    def save(self, config: dict) -> None:
        try:
            with open(self._config_path, "w") as f:
                json.dump(config, f, indent=4)
        except OSError as e:
            raise ConfigError(f"Failed to save config: {e}") from e

    def get_defaults(self) -> dict:
        return dict(DEFAULTS)
