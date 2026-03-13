import logging
import sys
import threading
import tkinter as tk
import customtkinter as ctk
from pathlib import Path

from ..models.file_result import FileResult
from ..models.processing_config import ProcessingConfig
from ..services.config_service import ConfigService
from ..services.processing_service import ProcessingService
from ..handlers.registry import HandlerRegistry
from .theme import (BG, BG_SURFACE, BG_INPUT, FG, FG_DIM, FG_HEADING,
                    ACCENT, ACCENT_HOVER, SUCCESS, BORDER)
from .format_help_window import show_format_help
from .widgets.directory_entry import DirectoryEntry
from .widgets.checkbutton_group import CheckbuttonGroup

logger = logging.getLogger(__name__)

FORMAT_HINT = "e.g. %Y/%m/%d \u2192 2024/01/15"

ctk.set_appearance_mode("dark")


class AppWindow(ctk.CTk):
    def __init__(self,
                 config_service: ConfigService,
                 processing_service: ProcessingService,
                 registry: HandlerRegistry):
        super().__init__(fg_color=BG)

        self._config_service = config_service
        self._processing_service = processing_service
        self._registry = registry
        self._processing = False

        self.title("Photo Sorter")
        w, h = 850, 450
        self.minsize(w, h)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Window icon — support both normal and PyInstaller-bundled paths
        base = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
        icon_path = base / "assets" / "logo.png"
        if icon_path.exists():
            self.iconbitmap(default="")
            icon = tk.PhotoImage(file=str(icon_path))
            self.iconphoto(True, icon)
            self._icon = icon  # prevent garbage collection

        self._build_ui()
        self._load_config()
        self._last_saved_config: dict = {}
        self._start_autosave()

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── UI Construction ────────────────────────────────────────

    def _build_ui(self) -> None:
        pad = {"padx": 20, "pady": (0, 4)}
        self.grid_columnconfigure(0, weight=1)

        # ── Directories ──
        dir_section = self._section(self, "Directories")
        dir_section.grid(row=0, column=0, sticky=tk.EW, **pad)

        dir_inner = ctk.CTkFrame(dir_section, fg_color=BG_SURFACE, corner_radius=8)
        dir_inner.pack(fill=tk.X, pady=(4, 0))
        dir_inner.grid_columnconfigure(0, weight=1)

        self._input_dir = DirectoryEntry(dir_inner, "Source:", on_change=self._update_file_count)
        self._input_dir.grid(row=0, column=0, sticky=tk.EW, padx=12, pady=(10, 4))

        self._output_dir = DirectoryEntry(dir_inner, "Output:")
        self._output_dir.grid(row=1, column=0, sticky=tk.EW, padx=12, pady=(4, 10))

        # ── File count indicator ──
        count_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=8)
        count_frame.grid(row=1, column=0, sticky=tk.EW, padx=20, pady=(4, 8))

        self._file_count_var = tk.StringVar(value="Select a source directory and file types")
        self._file_count_label = ctk.CTkLabel(count_frame, textvariable=self._file_count_var,
                                              font=ctk.CTkFont(size=13, weight="bold"),
                                              text_color=ACCENT)
        self._file_count_label.pack(anchor=tk.W, padx=12, pady=8)

        # ── Settings row: format (60%) + file types (40%) ──
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.grid(row=2, column=0, sticky=tk.EW, padx=20, pady=(0, 4))
        settings_frame.grid_columnconfigure(0, weight=60, uniform="settings")
        settings_frame.grid_columnconfigure(1, weight=40, uniform="settings")

        # Left column: date format + options
        left_col = ctk.CTkFrame(settings_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 6))

        # Date format
        fmt_section = self._section(left_col, "Date Format")
        fmt_section.pack(fill=tk.X)

        fmt_inner = ctk.CTkFrame(fmt_section, fg_color=BG_SURFACE, corner_radius=8)
        fmt_inner.pack(fill=tk.X, pady=(4, 0))

        fmt_row = ctk.CTkFrame(fmt_inner, fg_color="transparent")
        fmt_row.pack(fill=tk.X, padx=12, pady=(10, 4))
        fmt_row.grid_columnconfigure(0, weight=1)

        self._format_var = tk.StringVar(value="%Y/%m/%d")
        fmt_entry = ctk.CTkEntry(fmt_row, textvariable=self._format_var,
                                 font=ctk.CTkFont(family="Consolas", size=14),
                                 fg_color=BG_INPUT, border_color=BORDER,
                                 text_color=FG)
        fmt_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 6))

        help_btn = ctk.CTkButton(fmt_row, text="?", width=32,
                                 command=lambda: show_format_help(self),
                                 fg_color=BG_INPUT, hover_color=BORDER,
                                 text_color=FG_DIM, border_width=1, border_color=BORDER)
        help_btn.grid(row=0, column=1)

        ctk.CTkLabel(fmt_inner, text=FORMAT_HINT,
                     font=ctk.CTkFont(family="Consolas", size=11),
                     text_color=FG_DIM).pack(anchor=tk.W, padx=12, pady=(0, 10))

        # Options
        opts_section = self._section(left_col, "Options")
        opts_section.pack(fill=tk.X, pady=(8, 0))

        opts_inner = ctk.CTkFrame(opts_section, fg_color=BG_SURFACE, corner_radius=8)
        opts_inner.pack(fill=tk.X, pady=(4, 0))

        self._unknown_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(opts_inner, text="Move unknown dates to separate folder",
                        variable=self._unknown_var,
                        fg_color=ACCENT, hover_color=ACCENT,
                        text_color=FG).pack(anchor=tk.W, padx=12, pady=10)

        # File types (right column)
        types_section = self._section(settings_frame, "File Types")
        types_section.grid(row=0, column=1, sticky=tk.NSEW, padx=(6, 0))

        types_inner = ctk.CTkFrame(types_section, fg_color=BG_SURFACE, corner_radius=8)
        types_inner.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        self._file_types = CheckbuttonGroup(types_inner, self._registry.get_all_extensions(),
                                            on_change=self._update_file_count)
        self._file_types.pack(anchor=tk.W, padx=12, pady=10)

        # ── Actions ──
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=3, column=0, sticky=tk.EW, padx=20, pady=(12, 0))

        self._btn_copy = ctk.CTkButton(action_frame, text="Copy Files",
                                       command=self._on_copy,
                                       fg_color=BG_SURFACE, hover_color=BORDER,
                                       text_color=FG, border_width=1, border_color=BORDER,
                                       width=110)
        self._btn_copy.pack(side=tk.RIGHT, padx=(8, 0))

        self._btn_move = ctk.CTkButton(action_frame, text="Move Files",
                                       command=self._on_move,
                                       fg_color=ACCENT, hover_color=ACCENT_HOVER,
                                       text_color="#11111b",
                                       font=ctk.CTkFont(size=13, weight="bold"),
                                       width=120)
        self._btn_move.pack(side=tk.RIGHT)

        # ── Progress ──
        self._progress_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=8, height=36)
        self._progress_frame.grid(row=4, column=0, sticky=tk.EW, padx=20, pady=(12, 0))
        self._progress_frame.grid_remove()
        self._progress_frame.grid_columnconfigure(0, weight=1)

        self._progress_bar = ctk.CTkProgressBar(self._progress_frame,
                                                progress_color=SUCCESS,
                                                fg_color=BG_INPUT, height=16,
                                                corner_radius=4)
        self._progress_bar.grid(row=0, column=0, sticky=tk.EW, padx=12, pady=(8, 2))
        self._progress_bar.set(0)

        self._progress_label = ctk.CTkLabel(self._progress_frame, text="0/0",
                                            font=ctk.CTkFont(size=11, weight="bold"),
                                            text_color=FG_DIM)
        self._progress_label.grid(row=1, column=0, pady=(0, 6))

        self._processed_count = 0
        self._total_count = 0

        # ── Status bar ──
        status_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=0)
        status_frame.grid(row=5, column=0, sticky=tk.EW + tk.S, padx=0, pady=(12, 0))
        self.grid_rowconfigure(5, weight=1)

        self._status_var = tk.StringVar(value="Ready")
        ctk.CTkLabel(status_frame, textvariable=self._status_var,
                     font=ctk.CTkFont(size=11),
                     text_color=FG_DIM).pack(anchor=tk.W, padx=16, pady=6)

    def _section(self, parent, title: str) -> ctk.CTkFrame:
        """Create a section frame with a label header."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(frame, text=title,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=FG_HEADING).pack(anchor=tk.W)
        return frame

    # ── File count ─────────────────────────────────────────────

    def _update_file_count(self) -> None:
        if self._processing:
            return

        input_dir = self._input_dir.get()
        extensions = self._file_types.get_selected()

        if not input_dir or not Path(input_dir).is_dir() or not extensions:
            self._file_count_var.set("Select a source directory and file types")
            self._status_var.set("Ready")
            return

        ext_set = {f".{e.lower().lstrip('.')}" for e in extensions}
        count = sum(
            1 for f in Path(input_dir).rglob("*")
            if f.is_file() and f.suffix.lower() in ext_set
        )
        self._file_count_var.set(f"Found {count} file{'s' if count != 1 else ''}")
        self._status_var.set("Ready")

    # ── Config persistence ─────────────────────────────────────

    def _load_config(self) -> None:
        config = self._config_service.load()
        self._input_dir.set(config.get("input_dir", ""))
        self._output_dir.set(config.get("output_dir", ""))
        self._format_var.set(config.get("date_format", "%Y/%m/%d"))
        self._file_types.set_selected(config.get("selected_extensions", []))
        self._unknown_var.set(config.get("handle_unknown", True))

    def _get_current_config(self) -> dict:
        return {
            "input_dir": self._input_dir.get(),
            "output_dir": self._output_dir.get(),
            "date_format": self._format_var.get(),
            "selected_extensions": self._file_types.get_selected(),
            "handle_unknown": self._unknown_var.get(),
        }

    def _save_config(self) -> None:
        config = self._get_current_config()
        self._config_service.save(config)
        self._last_saved_config = config

    def _start_autosave(self) -> None:
        self._last_saved_config = self._get_current_config()
        self._autosave_tick()

    def _autosave_tick(self) -> None:
        current = self._get_current_config()
        if current != self._last_saved_config:
            self._save_config()
            logger.debug("Config auto-saved")
        self.after(10_000, self._autosave_tick)

    # ── Processing ─────────────────────────────────────────────

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
        from tkinter import messagebox

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
        from tkinter import messagebox

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
        self._btn_move.configure(state=tk.DISABLED)
        self._btn_copy.configure(state=tk.DISABLED)
        self._status_var.set("Processing...")

        self._processed_count = 0
        self._total_count = 0
        self._progress_bar.set(0)
        self._progress_label.configure(text="0/0")
        self._progress_frame.grid()
        logger.info("Starting %s operation", action)

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

        def on_total(total: int) -> None:
            self.after(0, self._on_total, total)

        results = self._processing_service.process(config, on_progress=on_progress,
                                                   on_total=on_total)
        self.after(0, self._on_complete, results)

    def _on_total(self, total: int) -> None:
        self._total_count = total
        self._progress_label.configure(text=f"0/{total}")

    def _on_progress(self, result: FileResult) -> None:
        self._processed_count += 1
        if self._total_count > 0:
            self._progress_bar.set(self._processed_count / self._total_count)
        self._progress_label.configure(text=f"{self._processed_count}/{self._total_count}")
        self._status_var.set(f"Processing: {result.source.name} \u2014 {result.status}")

    def _on_complete(self, results: list[FileResult]) -> None:
        from tkinter import messagebox

        self._processing = False
        self._btn_move.configure(state=tk.NORMAL)
        self._btn_copy.configure(state=tk.NORMAL)
        self._progress_frame.grid_remove()

        success = sum(1 for r in results if r.status == "success")
        unknown = sum(1 for r in results if r.status == "unknown")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")

        summary = f"Done! {success} sorted, {unknown} unknown, {skipped} skipped, {errors} errors."
        self._status_var.set(summary)
        logger.info(summary)

        messagebox.showinfo("Complete", summary)

    def _on_closing(self) -> None:
        from tkinter import messagebox

        if self._processing:
            messagebox.showwarning("Warning", "Processing is still running.")
            return
        self._save_config()
        self.destroy()
