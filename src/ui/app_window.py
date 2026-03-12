import threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from ..models.file_result import FileResult
from ..models.processing_config import ProcessingConfig
from ..services.config_service import ConfigService
from ..services.processing_service import ProcessingService
from ..handlers.registry import HandlerRegistry
from .widgets.directory_entry import DirectoryEntry
from .widgets.checkbutton_group import CheckbuttonGroup


FORMAT_TOOLTIP = """Strftime format codes:
%Y  Year (2024)        %m  Month (01-12)      %d  Day (01-31)
%H  Hour (00-23)       %M  Minute (00-59)     %S  Second (00-59)

Example: %Y/%m/%d -> 2024/01/15"""

UNKNOWN_TOOLTIP = """If checked, files without a detected date will be
moved to a dedicated folder (default: ".unknown").
If unchecked, those files will be left as-is."""


class AppWindow(tk.Tk):
    def __init__(self,
                 config_service: ConfigService,
                 processing_service: ProcessingService,
                 registry: HandlerRegistry):
        super().__init__()

        self._config_service = config_service
        self._processing_service = processing_service
        self._registry = registry
        self._processing = False

        self.title("Photo Sorter")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._build_ui()
        self._load_config()

    def _build_ui(self) -> None:
        # Directories
        dir_frame = tk.LabelFrame(self, text="Directories", padx=10, pady=10)
        dir_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self._input_dir = DirectoryEntry(dir_frame, "Input:")
        self._input_dir.pack(fill=tk.X, pady=2)

        self._output_dir = DirectoryEntry(dir_frame, "Output:")
        self._output_dir.pack(fill=tk.X, pady=2)

        # Format
        format_frame = tk.LabelFrame(self, text="Date Format", padx=10, pady=10)
        format_frame.pack(fill=tk.X, padx=10, pady=5)

        self._format_var = tk.StringVar(value="%Y/%m/%d")
        format_entry = tk.Entry(format_frame, textvariable=self._format_var, width=30, bg="light yellow")
        format_entry.pack(side=tk.LEFT, padx=(0, 10))

        format_help = tk.Label(format_frame, text=FORMAT_TOOLTIP, justify=tk.LEFT,
                               font=("Consolas", 8), fg="gray40")
        format_help.pack(side=tk.LEFT)

        # File types
        types_frame = tk.LabelFrame(self, text="File Types", padx=10, pady=10)
        types_frame.pack(fill=tk.X, padx=10, pady=5)

        self._file_types = CheckbuttonGroup(types_frame, self._registry.get_all_extensions())
        self._file_types.pack(fill=tk.X)

        # Options
        options_frame = tk.LabelFrame(self, text="Options", padx=10, pady=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        self._unknown_var = tk.BooleanVar(value=True)
        unknown_cb = tk.Checkbutton(options_frame, text="Move files with unknown dates to separate folder",
                                    variable=self._unknown_var)
        unknown_cb.pack(anchor=tk.W)

        # Action buttons
        btn_frame = tk.Frame(self, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)

        self._btn_move = tk.Button(btn_frame, text="Move Files", command=self._on_move, width=15)
        self._btn_move.pack(side=tk.LEFT, padx=(0, 10))

        self._btn_copy = tk.Button(btn_frame, text="Copy Files", command=self._on_copy, width=15)
        self._btn_copy.pack(side=tk.LEFT)

        # Status
        self._status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self, textvariable=self._status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10))

    def _load_config(self) -> None:
        config = self._config_service.load()
        self._input_dir.set(config.get("input_dir", ""))
        self._output_dir.set(config.get("output_dir", ""))
        self._format_var.set(config.get("date_format", "%Y/%m/%d"))
        self._file_types.set_selected(config.get("selected_extensions", []))
        self._unknown_var.set(config.get("handle_unknown", True))

    def _save_config(self) -> None:
        config = {
            "input_dir": self._input_dir.get(),
            "output_dir": self._output_dir.get(),
            "date_format": self._format_var.get(),
            "selected_extensions": self._file_types.get_selected(),
            "handle_unknown": self._unknown_var.get(),
        }
        self._config_service.save(config)

    def _build_config(self, action: str) -> ProcessingConfig:
        return ProcessingConfig(
            input_dir=Path(self._input_dir.get()),
            output_dir=Path(self._output_dir.get()),
            date_format=self._format_var.get(),
            action=action,
            selected_extensions=self._file_types.get_selected(),
            handle_unknown=self._unknown_var.get(),
        )

    def _validate(self) -> bool:
        input_dir = self._input_dir.get()
        output_dir = self._output_dir.get()

        if not input_dir or not output_dir:
            messagebox.showerror("Error", "Select input and output directories.")
            return False

        if not Path(input_dir).is_dir():
            messagebox.showerror("Error", "Input directory does not exist.")
            return False

        if not self._file_types.get_selected():
            messagebox.showerror("Error", "Select at least one file type.")
            return False

        return True

    def _on_move(self) -> None:
        self._start_processing("move")

    def _on_copy(self) -> None:
        self._start_processing("copy")

    def _start_processing(self, action: str) -> None:
        if self._processing:
            return

        if not self._validate():
            return

        ok = messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to {action} the selected files?",
            default="no",
        )
        if not ok:
            return

        self._processing = True
        self._btn_move.config(state=tk.DISABLED)
        self._btn_copy.config(state=tk.DISABLED)
        self._status_var.set("Processing...")

        config = self._build_config(action)

        thread = threading.Thread(
            target=self._run_processing,
            args=(config,),
            daemon=True,
        )
        thread.start()

    def _run_processing(self, config: ProcessingConfig) -> None:
        def on_progress(result: FileResult) -> None:
            self.after(0, self._on_progress, result)

        results = self._processing_service.process(config, on_progress=on_progress)
        self.after(0, self._on_complete, results)

    def _on_progress(self, result: FileResult) -> None:
        self._status_var.set(f"Processing: {result.source.name} - {result.status}")

    def _on_complete(self, results: list[FileResult]) -> None:
        self._processing = False
        self._btn_move.config(state=tk.NORMAL)
        self._btn_copy.config(state=tk.NORMAL)

        success = sum(1 for r in results if r.status == "success")
        unknown = sum(1 for r in results if r.status == "unknown")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")

        summary = f"Done! {success} sorted, {unknown} unknown, {skipped} skipped, {errors} errors."
        self._status_var.set(summary)

        messagebox.showinfo("Complete", summary)

    def _on_closing(self) -> None:
        if self._processing:
            messagebox.showwarning("Warning", "Processing is still running.")
            return
        self._save_config()
        self.destroy()
