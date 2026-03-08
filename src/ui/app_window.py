"""Main application window."""
import tkinter as tk
from tkinter import filedialog, message as tk_messagebox
from pathlib import Path
import os

from .constants import FORMAT_TOOLTIPTEXT, UNKNOWN_TOOLTIP, INVALID_FORMAT_CHARS


class AppWindow(tk.Tk):
    """Main application window with all UI components."""

    def __init__(self, supported_file_types: list[str]):
        """Initialize the application window.

        Args:
            supported_file_types: List of supported file extensions.
        """
        super().__init__()
        self.title("File Sorter")
        self.geometry("700x640")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.supported_file_types = supported_file_types
        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the user interface."""
        # Input directory
        self.input_label = tk.Label(self, text="Input Directory")
        self.input_entry_var = tk.StringVar()
        self.input_entry = tk.Entry(self, textvariable=self.input_entry_var, width=40, bg="light yellow")
        self.input_browse_btn = tk.Button(self, text="Browse", command=self.browse_input)

        self.input_label.grid(row=1, column=0, padx=5, pady=5)
        self.input_entry.grid(row=1, column=1, padx=5, pady=5)
        self.input_browse_btn.grid(row=1, column=2)

        # Output directory
        self.output_label = tk.Label(self, text="Output Directory")
        self.output_entry_var = tk.StringVar()
        self.output_entry = tk.Entry(self, textvariable=self.output_entry_var, width=40, bg="light yellow")
        self.output_browse_btn = tk.Button(self, text="Browse", command=self.browse_output)

        self.output_label.grid(row=2, column=0, padx=5, pady=5)
        self.output_entry.grid(row=2, column=1, padx=5, pady=5)
        self.output_browse_btn.grid(row=2, column=2)

        # Input format
        self.format_label = tk.Label(self, text="Input format")
        self.format_entry_var = tk.StringVar(value="%%Y%%m%%d")
        self.format_entry = tk.Entry(self, textvariable=self.format_entry_var, width=40, bg="light yellow")
        self.format_label.grid(row=3, column=0, padx=5, pady=5)
        self.format_entry.grid(row=3, column=1, padx=5, pady=5)

        # File type checkbuttons
        self.type_checkbuttons = []
        for pos, filetype in enumerate(self.supported_file_types):
            cb = tk.Checkbutton(self, text=filetype)
            cb.grid(column=10, row=pos, sticky="w")
            self.type_checkbuttons.append(cb)

        # Unknown data checkbox
        self.unknown_check_var = tk.IntVar(value=0)
        self.unknown_check = tk.Checkbutton(
            self,
            text="Move Unknown Data?",
            variable=self.unknown_check_var,
            command=self.unknown_check_callback,
        )
        self.unknown_check.grid(row=4, column=1, padx=5, pady=5)

        # Action buttons
        self.btn_move = tk.Button(self, text="Move", command=self.action_move)
        self.btn_copy = tk.Button(self, text="Copy", command=self.action_copy)
        self.btn_move.grid(row=5, column=1, padx=10, pady=10)
        self.btn_copy.grid(row=5, column=2, padx=10, pady=10)

        # Separator
        tk.Canvas(self, background="black", width=500, height=2).grid(
            row=6, column=0, columnspan=5
        )

        # Tooltips
        format_tooltip = Hovertip(self.format_entry, FORMAT_TOOLTIPTEXT)
        unknown_tooltip = Hovertip(self.unknown_check, UNKNOWN_TOOLTIP)

    def browse_input(self) -> None:
        """Browse for input directory."""
        filename = filedialog.askdirectory(initialdir="/", title="Select a folder")
        if filename:
            self.input_entry_var.set(filename)

    def browse_output(self) -> None:
        """Browse for output directory."""
        filename = filedialog.askdirectory(initialdir="/", title="Select a folder")
        if filename:
            self.output_entry_var.set(filename)

    def unknown_check_callback(self) -> None:
        """Handle unknown data checkbox state change."""
        pass

    def action_move(self) -> None:
        """Handle move action."""
        self.process_selection("move")

    def action_copy(self) -> None:
        """Handle copy action."""
        self.process_selection("copy")

    def process_selection(self, action: str) -> None:
        """Process selected files.

        Args:
            action: Either "move" or "copy".
        """
        input_dir = self.input_entry_var.get()
        output_dir = self.output_entry_var.get()
        input_format = self.format_entry_var.get()
        move_unknown = self.unknown_check_var.get() == 1

        if not input_dir or not output_dir:
            tk_messagebox.showerror("Error", "Please select input and output directories")
            return

        # Validate paths
        if not os.path.isdir(input_dir):
            tk_messagebox.showerror("Error", "Input path is invalid")
            return

        if not output_dir or not self.is_path_creatable(output_dir):
            tk_messagebox.showerror("Error", "Output path is invalid or not writable")
            return

        if any(c in input_format for c in INVALID_FORMAT_CHARS):
            tk_messagebox.showerror("Error", "Input format is invalid")
            return

        # Get file extensions from selected checkbuttons
        selected_extensions = [cb.cget("text") for cb in self.type_checkbuttons if cb.selected]
        if not selected_extensions:
            tk_messagebox.showerror("Error", "Please select at least one file type")
            return

        # Import here to avoid circular imports
        from ..core.meta_data_reader import get_matching_files, get_file_date

        # Process files
        for file_path in get_matching_files(input_dir, selected_extensions):
            file_ext = Path(file_path).suffix.lower()

            if file_ext in [".jpg", ".jpeg", ".webp", ".png"]:
                date_str = get_file_date(file_path)
            else:
                from ..core.meta_data_reader import get_video_date
                exiftool_path = self.get_exiftool_path()
                date_str = get_video_date(file_path, exiftool_path)

            # Handle unknown data
            if date_str is None:
                if move_unknown:
                    dest = os.path.join(output_dir, ".unknown")
                    from ..core.file_operations import move_file
                    move_file(file_path, dest)
                continue

            # Parse date and move/copy
            try:
                from datetime import datetime as dt
                dt_obj = dt.strptime(date_str[:19], "%Y:%m:%d %H:%M:%S")
                folder_name = dt_obj.strftime(input_format)
                dest_dir = os.path.join(output_dir, folder_name)

                from ..core.file_operations import move_file as file_move, copy_file as file_copy
                action_func = file_move if action == "move" else file_copy
                action_func(file_path, dest_dir)
            except ValueError:
                if move_unknown:
                    dest = os.path.join(output_dir, ".unknown")
                    from ..core.file_operations import move_file
                    move_file(file_path, dest)

    def get_exiftool_path(self) -> str | None:
        """Get path to exiftool.exe."""
        app_dir = Path(__file__).parent.parent.parent
        exiftool_path = app_dir / "exiftool" / "exiftool64.exe"

        if exiftool_path.exists():
            return str(exiftool_path)

        alt_path = app_dir / "exiftool.exe"
        if alt_path.exists():
            return str(alt_path)

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

    def on_closing(self) -> bool:
        """Handle window close event.

        Returns:
            False to prevent closing.
        """
        return True


class Hovertip:
    """Tooltip class imported from tkinter."""
    pass
