"""Main application module."""

import os
from pathlib import Path
from datetime import datetime
import subprocess
from tkinter import messagebox

from utils.path_utils import is_path_creatable
from .config.config_manager import Config
from .core.meta_data_reader import get_matching_files, get_file_date
from .core.file_operations import move_file, copy_file
from .ui.app_window import AppWindow


class PhotoSorterApp(AppWindow):
    """Main Photo Sorter application."""

    SUPPORTED_TYPES = ["jpg", "png", "webp", "mov", "avi", "mp4"]

    def __init__(self):
        super().__init__(self.SUPPORTED_TYPES)
        self.config = Config()
        self.load_config()

    # -------------------------
    # Config
    # -------------------------

    def load_config(self) -> None:
        """Load selected file types from config."""
        selected = {t.lower() for t in self.config.used_file_types}

        for cb in self.type_checkbuttons:
            if cb.cget("text").lower() in selected:
                cb.select()

    # -------------------------
    # UI Actions
    # -------------------------

    def action_move(self) -> None:
        self.confirm_and_process("move")

    def action_copy(self) -> None:
        self.confirm_and_process("copy")

    def confirm_and_process(self, action: str) -> None:
        """Confirm user action then process files."""
        ok = messagebox.askyesno(
            "Confirm",
            "Make sure all settings are correct before continuing.",
            default="no",
        )

        if ok:
            self.process_files(action)

    # -------------------------
    # Validation
    # -------------------------

    def validate_inputs(self) -> bool:
        """Validate user inputs."""

        if not self.config.input_dir or not self.config.output_dir:
            messagebox.showerror("Error", "Select input and output directories")
            return False

        if not os.path.isdir(self.config.input_dir):
            messagebox.showerror("Error", "Input directory is invalid")
            return False

        if not is_path_creatable(self.config.output_dir):
            messagebox.showerror("Error", "Output directory not createAble")
            return False

        invalid_chars = '/><:"\\|?*'
        if any(c in self.config.input_format for c in invalid_chars):
            messagebox.showerror("Error", "Folder format contains invalid characters")
            return False

        if not self.get_selected_extensions():
            messagebox.showerror("Error", "Select at least one file type")
            return False

        return True

    # -------------------------
    # File Processing
    # -------------------------

    def process_files(self, action: str) -> None:
        """Process files (move or copy)."""

        if not self.validate_inputs():
            return

        action_func = move_file if action == "move" else copy_file
        unknown_dir = os.path.join(self.config.output_dir, ".unknown")

        for file_path in get_matching_files(
            self.config.input_dir,
            self.get_selected_extensions(),
        ):
            dest = self.get_destination(file_path)

            if dest is None:
                self.handle_unknown(file_path, unknown_dir)
                continue

            try:
                action_func(file_path, dest)
            except Exception:
                self.handle_unknown(file_path, unknown_dir)

    # -------------------------
    # Destination Logic
    # -------------------------

    def get_destination(self, file_path: str) -> str | None:
        """Determine destination directory."""

        date_str = self.get_file_date(file_path)
        if not date_str:
            return None

        try:
            dt_obj = datetime.strptime(date_str[:19], "%Y:%m:%d %H:%M:%S")
            folder = dt_obj.strftime(self.config.input_format)
            return os.path.join(self.config.output_dir, folder)

        except ValueError:
            return None

    def handle_unknown(self, file_path: str, unknown_dir: str) -> None:
        """Move file to unknown folder if enabled."""

        if self.config.move_unknown_to_folder:
            move_file(file_path, unknown_dir)

    # -------------------------
    # Metadata
    # -------------------------

    def get_file_date(self, file_path: str) -> str | None:
        """Extract date from file."""
        ext = Path(file_path).suffix.lower()

        if ext in {".jpg", ".jpeg", ".webp", ".png"}:
            return get_file_date(file_path)

        return self.get_video_date(file_path)

    def get_video_date(self, video_path: str) -> str | None:
        """Extract video date using ExifTool."""

        exiftool = self.get_exiftool_path()
        if not exiftool:
            return None

        try:
            result = subprocess.check_output(
                [exiftool, video_path],
                text=True,
                stderr=subprocess.DEVNULL,
            )

            for line in result.splitlines():
                if "Create Date" in line:
                    return line.split(":", 1)[1].strip()

        except Exception:
            pass

        return None

    def get_exiftool_path(self) -> str | None:
        """Locate exiftool executable."""

        app_dir = Path(__file__).resolve().parents[2]

        for path in [
            app_dir / "exiftool" / "exiftool64.exe",
            app_dir / "exiftool.exe",
        ]:
            if path.exists():
                return str(path)

        return None

    # -------------------------
    # Helpers
    # -------------------------

    def get_selected_extensions(self) -> list[str]:
        """Return selected file extensions."""
        return [cb.cget("text") for cb in self.type_checkbuttons if cb.selected]


def main() -> None:
    app = PhotoSorterApp()
    app.run()


if __name__ == "__main__":
    main()