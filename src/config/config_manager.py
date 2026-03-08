"""Configuration handling for the application."""
import configparser
from pathlib import Path


class Config:
    """Application configuration manager.

    Handles loading and saving of configuration values from config.ini.
    Provides a simple dictionary-like interface for common operations.
    """

    def __init__(self, config_path: str | None = None):
        """Initialize Config.

        Args:
            config_path: Path to config.ini file. If None, uses path relative to app root.
        """
        if config_path is None:
            this_folder = Path(__file__).parent.parent
            self.config_path = this_folder / "config.ini"
        else:
            self.config_path = Path(config_path)

        self.config = configparser.ConfigParser()
        self._ensure_config_exists()
        self._load()

    def _ensure_config_exists(self) -> None:
        """Create config file if it doesn't exist."""
        if not self.config_path.exists():
            self.config.add_section("main")
            self._set("main", "used_file_types", "[]")
            self._set("main", "textbox_input_dir", "")
            self._set("main", "textbox_output_dir", "")
            self._set("main", "textbox_input_format", "")
            self._set("main", "checkbutton_unknowdata_checkvar", "0")

    def _load(self) -> None:
        """Load configuration from file."""
        self.config.read(self.config_path)

    def _save(self) -> None:
        """Save configuration to file."""
        with open(self.config_path, "w") as f:
            self.config.write(f)

    def _get(self, section: str, key: str, default: str = "") -> str:
        """Get config value.

        Args:
            section: Config section name.
            key: Config key name.
            default: Default value if key not found.

        Returns:
            Config value or default.
        """
        return self.config.get(section, key, fallback=default)

    def _set(self, section: str, key: str, value: str) -> None:
        """Set config value.

        Args:
            section: Config section name.
            key: Config key name.
            value: Value to set.
        """
        self.config.set(section, key, value)
        self._save()

    # Property getters and setters

    @property
    def used_file_types(self) -> list[str]:
        """Get list of supported file types."""
        raw = self._get("main", "used_file_types", "[]")
        if raw.startswith("[") and raw.endswith("]"):
            return [n.strip().strip("'\"") for n in raw[1:-1].split(",") if n.strip()]
        return []

    @used_file_types.setter
    def used_file_types(self, value: list[str]) -> None:
        self._set("main", "used_file_types", str(value))

    @property
    def input_dir(self) -> str:
        """Get input directory path."""
        return self._get("main", "textbox_input_dir", "")

    @input_dir.setter
    def input_dir(self, value: str) -> None:
        self._set("main", "textbox_input_dir", value)

    @property
    def output_dir(self) -> str:
        """Get output directory path."""
        return self._get("main", "textbox_output_dir", "")

    @output_dir.setter
    def output_dir(self, value: str) -> None:
        self._set("main", "textbox_output_dir", value)

    @property
    def input_format(self) -> str:
        """Get input date format."""
        return self._get("main", "textbox_input_format", "")

    @input_format.setter
    def input_format(self, value: str) -> None:
        self._set("main", "textbox_input_format", value.replace("%", "%%"))

    @property
    def move_unknown_to_folder(self) -> bool:
        """Get whether to move unknown data to .unknown folder."""
        return self._get("main", "checkbutton_unknowdata_checkvar", "0") == "1"

    @move_unknown_to_folder.setter
    def move_unknown_to_folder(self, value: bool) -> None:
        self._set("main", "checkbutton_unknowdata_checkvar", str(1 if value else "0"))

    def reset(self) -> None:
        """Reset to default configuration."""
        self.config.add_section("main")
        self._set("main", "used_file_types", "[]")
        self._set("main", "textbox_input_dir", "")
        self._set("main", "textbox_output_dir", "")
        self._set("main", "textbox_input_format", "")
        self._set("main", "checkbutton_unknowdata_checkvar", "0")
        self._save()
