import logging
import sys
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from pathlib import Path

from ..services.config_service import ConfigService
from ..services.log_service import LogService
from ..services.processing_service import ProcessingService
from ..handlers.registry import HandlerRegistry
from .theme import (BG, BG_SURFACE, BG_INPUT, FG, FG_DIM, FG_HEADING,
                    ACCENT, ACCENT_HOVER, SUCCESS, BORDER)
from .format_help_window import show_format_help
from .widgets.directory_entry import DirectoryEntry
from .widgets.checkbutton_group import CheckbuttonGroup
from .file_counter import FileCounter
from .processing_controller import ProcessingController

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
        self._log_service = LogService()
        self._registry = registry

        self.title("Photo Sorter")
        w, h = 850, 475
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
        self._init_controllers()
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

        self._input_dir = DirectoryEntry(dir_inner, "Source:", on_change=self._on_input_changed)
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
                                            on_change=self._on_input_changed)
        self._file_types.pack(anchor=tk.W, padx=12, pady=10)

        # ── Progress ──
        self._progress_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=8, height=36)
        self._progress_frame.grid(row=3, column=0, sticky=tk.EW, padx=20, pady=(12, 0))
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
        self._progress_label.grid(row=1, column=0, pady=(0, 2))

        # Timing line: elapsed, ETA, throughput
        self._timing_label = ctk.CTkLabel(self._progress_frame, text="",
                                          font=ctk.CTkFont(size=11),
                                          text_color=FG_DIM)
        self._timing_label.grid(row=2, column=0, pady=(0, 2))

        # Status breakdown: success/unknown/skipped/error counters
        self._breakdown_label = ctk.CTkLabel(self._progress_frame, text="",
                                             font=ctk.CTkFont(size=11),
                                             text_color=FG_DIM)
        self._breakdown_label.grid(row=3, column=0, pady=(0, 2))

        # Current file line: source -> destination
        self._current_file_label = ctk.CTkLabel(self._progress_frame, text="",
                                                font=ctk.CTkFont(size=11),
                                                text_color=FG_DIM)
        self._current_file_label.grid(row=4, column=0, pady=(0, 6))

        # ── Tree Preview Panel (hidden by default) ──
        self._tree_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=8)
        self._tree_frame.grid(row=4, column=0, sticky=tk.NSEW, padx=20, pady=(12, 0))
        self._tree_frame.grid_remove()
        self._tree_frame.grid_columnconfigure(0, weight=1)
        self._tree_frame.grid_rowconfigure(0, weight=1)

        # Configure ttk style for treeview to match dark theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=BG_INPUT,
                        foreground=FG,
                        fieldbackground=BG_INPUT,
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background=BG_SURFACE,
                        foreground=FG_HEADING)
        style.map("Treeview", background=[("selected", ACCENT)])

        self._tree_view = ttk.Treeview(self._tree_frame, show="tree", selectmode="none")
        self._tree_view.grid(row=0, column=0, sticky=tk.NSEW, padx=12, pady=(8, 4))

        tree_scroll = ttk.Scrollbar(self._tree_frame, orient=tk.VERTICAL, command=self._tree_view.yview)
        tree_scroll.grid(row=0, column=1, sticky=tk.NS, pady=(8, 4))
        self._tree_view.configure(yscrollcommand=tree_scroll.set)

        self._tree_summary_label = ctk.CTkLabel(self._tree_frame, text="",
                                                 font=ctk.CTkFont(size=12, weight="bold"),
                                                 text_color=FG_DIM)
        self._tree_summary_label.grid(row=1, column=0, columnspan=2, pady=(4, 8))

        # ── Actions ──
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=5, column=0, sticky=tk.EW, padx=20, pady=(12, 0))

        self._btn_copy = ctk.CTkButton(action_frame, text="Copy Files",
                                       command=lambda: self._processor.start("copy"),
                                       fg_color=BG_SURFACE, hover_color=BORDER,
                                       text_color=FG, border_width=1, border_color=BORDER,
                                       width=110)
        self._btn_copy.pack(side=tk.RIGHT, padx=(8, 0))

        self._btn_move = ctk.CTkButton(action_frame, text="Move Files",
                                       command=lambda: self._processor.start("move"),
                                       fg_color=ACCENT, hover_color=ACCENT_HOVER,
                                       text_color="#11111b",
                                       font=ctk.CTkFont(size=13, weight="bold"),
                                       width=120)
        self._btn_move.pack(side=tk.RIGHT)

        self._btn_dry_run = ctk.CTkButton(action_frame, text="Dry Run",
                                          command=self._on_dry_run_click,
                                          fg_color=BG_SURFACE, hover_color=BORDER,
                                          text_color=FG, border_width=1, border_color=BORDER,
                                          width=100)
        self._btn_dry_run.pack(side=tk.RIGHT, padx=(0, 8))

        # ── Status bar ──
        status_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, corner_radius=0)
        status_frame.grid(row=6, column=0, sticky=tk.EW + tk.S, padx=0, pady=(12, 0))
        self.grid_rowconfigure(4, weight=1)

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

    # ── Controllers ─────────────────────────────────────────────

    def _init_controllers(self) -> None:
        self._processor = ProcessingController(
            window=self,
            processing_service=self._processing_service,
            log_service=self._log_service,
            get_input_dir=self._input_dir.get,
            get_output_dir=self._output_dir.get,
            get_extensions=self._file_types.get_selected,
            get_format=self._format_var.get,
            get_unknown=self._unknown_var.get,
            btn_move=self._btn_move,
            btn_copy=self._btn_copy,
            btn_dry_run=self._btn_dry_run,
            progress_frame=self._progress_frame,
            progress_bar=self._progress_bar,
            progress_label=self._progress_label,
            timing_label=self._timing_label,
            breakdown_label=self._breakdown_label,
            current_file_label=self._current_file_label,
            tree_frame=self._tree_frame,
            tree_view=self._tree_view,
            tree_summary_label=self._tree_summary_label,
            status_var=self._status_var,
        )

        self._counter = FileCounter(
            window=self,
            file_count_var=self._file_count_var,
            status_var=self._status_var,
            get_input_dir=self._input_dir.get,
            get_extensions=self._file_types.get_selected,
            is_processing=lambda: self._processor.is_processing,
        )

    def _on_input_changed(self) -> None:
        self._counter.schedule()

    def _on_dry_run_click(self) -> None:
        """Handle dry run button click - start or stop dry run."""
        if self._processor._dry_run_active:
            self._processor.stop_dry_run()
        else:
            self._processor.start_dry_run()

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

    # ── Lifecycle ──────────────────────────────────────────────

    def _on_closing(self) -> None:
        from tkinter import messagebox

        if self._processor.is_processing:
            messagebox.showwarning("Warning", "Processing is still running.")
            return
        self._save_config()
        self.destroy()
