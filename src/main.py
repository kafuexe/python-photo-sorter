"""Main application module.

This module provides the PhotoSorterApp class that orchestrates the application.
"""
import os
from pathlib import Path

from .config.config_manager import Config
from .core.meta_data_reader import get_matching_files, get_file_date
from .core.file_operations import move_file, copy_file
from .ui.app_window import AppWindow
from tkinter import messagebox as tk_messagebox
from datetime import datetime as dt


class PhotoSorterApp(AppWindow):
    """Main application class.

    This class handles:
    - Configuration loading/saving
    - File processing workflow
    - User interface management
    """

    SUPPORTED_FILE_TYPES = ["jpg", "png", "wepg", "mov", "avi", "mp4"]

    def __init__(self):
        """Initialize the application."""
        super().__init__(self.SUPPORTED_FILE_TYPES)
        self.config = Config()
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from config.ini."""
        self.config.input_dir = self.config.input_dir
        self.config.output_dir = self.config.output_dir
        self.config.input_format = self.config.input_format
        self.config.move_unknown_to_folder = self.config.move_unknown_to_folder

        # Load file types from config
        saved_types = self.config.used_file_types
        for cb, ext in zip(self.type_checkbuttons, saved_types):
            if cb.cget("text").lower() == ext.lower():
                cb.select()

    def action_move(self) -> None:
        """Handle move action."""
        response = tk_messagebox.askyesno(
            title="Are you Sure?",
            message="""One last time before moving files, make sure all
            settings are correct, if you are sure click yes""",
            default="no",
        )
        if response:
            self.process_files("move")

    def action_copy(self) -> None:
        """Handle copy action."""
        response = tk_messagebox.askyesno(
            title="Are you Sure?",
            message="""One last time before copying files, make sure all
            settings are correct, if you are sure click yes""",
            default="no",
        )
        if response:
            self.process_files("copy")

    def process_files(self, action: str) -> None:
        """Process files from input directory.

        Args:
            action: Either "move" or "copy".
        """
        input_dir = self.config.input_dir
        output_dir = self.config.output_dir
        input_format = self.config.input_format
        move_unknown = self.config.move_unknown_to_folder

        if not input_dir or not output_dir:
            tk_messagebox.showerror("Error", "Please select input and output directories")
            return

        if not os.path.isdir(input_dir):
            tk_messagebox.showerror("Error", "Input path is invalid")
            return

        if not output_dir or not self.is_path_creatable(output_dir):
            tk_messagebox.showerror("Error", "Output path is invalid or not writable")
            return

        if any(
            c in input_format
            for c in ["/", ">", "<", ":", '"', "\\", "|", "?", "*"]
        ):
            tk_messagebox.showerror("Error", "Input format is invalid")
            return

        # Get file extensions from selected checkbuttons
        selected_extensions = self.get_selected_extensions()
        if not selected_extensions:
            tk_messagebox.showerror("Error", "Please select at least one file type")
            return

        # Process files
        for file_path in get_matching_files(input_dir, selected_extensions):
            file_ext = Path(file_path).suffix.lower()

            # Get date from file
            if file_ext in [".jpg", ".jpeg", ".webp", ".png"]:
                date_str = get_file_date(file_path)
            else:
                exiftool_path = self.get_exiftool_path()
                date_str = self.get_video_date(file_path, exiftool_path)

            # Handle unknown data
            if date_str is None:
                if move_unknown:
                    dest = os.path.join(output_dir, ".unknown")
                    move_file(file_path, dest)
                continue

            # Parse date
            try:
                date_str = date_str[:19]
                dt_obj = dt.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                folder_name = dt_obj.strftime(input_format)
                dest_dir = os.path.join(output_dir, folder_name)
            except ValueError:
                if move_unknown:
                    dest = os.path.join(output_dir, ".unknown")
                    move_file(file_path, dest)
                continue

            # Process file
            action_func = move_file if action == "move" else copy_file
            try:
                action_func(file_path, dest_dir)
            except Exception:
                if move_unknown:
                    dest = os.path.join(output_dir, ".unknown")
                    move_file(file_path, dest)

    def get_selected_extensions(self) -> list[str]:
        """Get list of selected file extensions.

        Returns:
            List of selected file extension strings.
        """
        return [cb.cget("text") for cb in self.type_checkbuttons if cb.selected]

    def get_exiftool_path(self) -> str | None:
        """Get path to exiftool.exe.

        Returns:
            Path to exiftool or None.
        """
        app_dir = Path(__file__).parent.parent.parent
        exiftool_path = app_dir / "exiftool" / "exiftool64.exe"

        if exiftool_path.exists():
            return str(exiftool_path)

        # Try alternative path
        alt_path = app_dir / "exiftool.exe"
        if alt_path.exists():
            return str(alt_path)

        return None

    def get_video_date(self, video_path: str, exiftool_path: str) -> str | None:
        """Extract date from video file using ExifTool.

        Args:
            video_path: Path to the video file.
            exiftool_path: Path to exiftool.exe.

        Returns:
            Date string or None.
        """
        try:
            result = os.popen(f'{exiftool_path}" "{video_path}"').read()
            for line in result.split("\n"):
                if "Create Date" in line:
                    date_str = line.split(":")[1].strip()
                    return date_str
        except Exception:
            pass
        return None

    def is_path_creatable(self, pathname: str) -> bool:
        """Check if path is creatable.

        Args:
            pathname: Path to check.

        Returns:
            True if path is valid and writable.
        """
        try:
            dirname = os.path.dirname(pathname) or os.getcwd()
            return os.access(dirname, os.W_OK)
        except OSError:
            return False

    def save_config(self) -> None:
        """Save current configuration."""
        selected = self.get_selected_extensions()
        self.config.used_file_types = selected
        self.config.input_dir = self.config.input_dir
        self.config.output_dir = self.config.output_dir
        self.config.input_format = self.format_entry_var.get().replace("%", "%%")
        self.config.move_unknown_to_folder = self.unknown_check_var.get() == 1

        self.config._save()

    def on_closing(self) -> bool:
        """Handle window close event.

        Returns:
            False to prevent closing.
        """
        self.save_config()
        return True


def main() -> None:
    """Main entry point."""
    app = PhotoSorterApp()
    app.run()


if __name__ == "__main__":
    main()
