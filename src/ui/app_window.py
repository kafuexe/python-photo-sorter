import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from ..models.file_result import FileResult
from ..models.processing_config import ProcessingConfig
from ..services.config_service import ConfigService
from ..services.processing_service import ProcessingService
from ..handlers.registry import HandlerRegistry
from .widgets.directory_entry import DirectoryEntry
from .widgets.checkbutton_group import CheckbuttonGroup

logger = logging.getLogger(__name__)

FORMAT_HINT = "e.g. %Y/%m/%d \u2192 2024/01/15"

FORMAT_REFERENCE = [
    ("Common codes", [
        ("%d", "Day of month", "01\u201331"),
        ("%m", "Month number", "01\u201312"),
        ("%y", "Year (short)", "24"),
        ("%Y", "Year (full)", "2024"),
        ("%H", "Hour (24h)", "00\u201323"),
        ("%I", "Hour (12h)", "01\u201312"),
        ("%M", "Minute", "00\u201359"),
        ("%S", "Second", "00\u201359"),
        ("%p", "AM / PM", "PM"),
    ]),
    ("Names", [
        ("%a", "Weekday (short)", "Wed"),
        ("%A", "Weekday (full)", "Wednesday"),
        ("%b", "Month (short)", "Dec"),
        ("%B", "Month (full)", "December"),
    ]),
    ("Other", [
        ("%j", "Day of year", "001\u2013366"),
        ("%U", "Week number (Sun)", "00\u201353"),
        ("%W", "Week number (Mon)", "00\u201353"),
        ("%f", "Microsecond", "000000\u2013999999"),
        ("%z", "UTC offset", "+0100"),
        ("%Z", "Timezone", "CST"),
        ("%%", "Literal %", "%"),
    ]),
]

# ── Color palette ──────────────────────────────────────────────
BG = "#1b1b1d"
BG_SURFACE = "#242428"
BG_INPUT = "#2c2c31"
FG = "#e4e4e7"
FG_DIM = "#8b8b93"
FG_HEADING = "#ffffff"
ACCENT = "#4f7cff"
ACCENT_HOVER = "#3d63d6"
SUCCESS = "#3ba55d"
WARN = "#d29922"
ERROR = "#e5533d"
BORDER = "#3a3a40"


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
        self.configure(bg=BG)
        self.minsize(620, 480)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._configure_styles()
        self._build_ui()
        self._load_config()
        self._last_saved_config: dict = {}
        self._start_autosave()

    # ── Styles ─────────────────────────────────────────────────

    def _configure_styles(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure(".", background=BG, foreground=FG, borderwidth=0,
                     font=("Segoe UI", 10))

        # Frames & label-frames
        s.configure("TFrame", background=BG)
        s.configure("Surface.TFrame", background=BG_SURFACE)
        s.configure("TLabelframe", background=BG, foreground=FG_DIM,
                     bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
        s.configure("TLabelframe.Label", background=BG, foreground=FG_HEADING,
                     font=("Segoe UI Semibold", 10))

        # Labels
        s.configure("TLabel", background=BG, foreground=FG)
        s.configure("Surface.TLabel", background=BG_SURFACE, foreground=FG)
        s.configure("Heading.TLabel", background=BG, foreground=FG_HEADING,
                     font=("Segoe UI", 18, "bold"))
        s.configure("Subheading.TLabel", background=BG, foreground=FG_DIM,
                     font=("Segoe UI", 9))
        s.configure("Help.TLabel", background=BG, foreground=FG_DIM,
                     font=("Consolas", 9))
        s.configure("FileCount.TLabel", background=BG_SURFACE, foreground=ACCENT,
                     font=("Segoe UI Semibold", 11))
        s.configure("Status.TLabel", background=BG_SURFACE, foreground=FG_DIM,
                     font=("Segoe UI", 9))

        # Entries
        s.configure("TEntry", fieldbackground=BG_INPUT, foreground=FG,
                     insertcolor=FG, bordercolor=BORDER, lightcolor=BORDER,
                     darkcolor=BORDER)
        s.map("TEntry", fieldbackground=[("focus", BG_INPUT)],
              bordercolor=[("focus", ACCENT)])

        # Buttons
        s.configure("TButton", background=BG_SURFACE, foreground=FG,
                     bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                     padding=(12, 6), font=("Segoe UI", 9))
        s.map("TButton",
              background=[("active", BORDER), ("disabled", BG)],
              foreground=[("disabled", FG_DIM)])

        s.configure("Action.TButton", background=ACCENT, foreground="#11111b",
                     font=("Segoe UI Semibold", 10), padding=(20, 8))
        s.map("Action.TButton",
              background=[("active", ACCENT_HOVER), ("disabled", BORDER)],
              foreground=[("disabled", FG_DIM)])

        # Checkbuttons
        s.configure("TCheckbutton", background=BG, foreground=FG,
                     font=("Segoe UI", 9))
        s.map("TCheckbutton", background=[("active", BG)])

        # Progressbar
        s.configure("TProgressbar", background=ACCENT, troughcolor=BG_SURFACE,
                     bordercolor=BG, lightcolor=ACCENT, darkcolor=ACCENT)

        # Separator
        s.configure("TSeparator", background=BORDER)

    # ── UI Construction ────────────────────────────────────────

    def _build_ui(self) -> None:
        pad = {"padx": 20, "pady": (0, 4)}
        self.columnconfigure(0, weight=1)

        # ── Header ──
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky=tk.EW, padx=20, pady=(20, 12))

        ttk.Label(header, text="Photo Sorter", style="Heading.TLabel").pack(anchor=tk.W)
        ttk.Label(header, text="Organize photos & videos by date into tidy folders",
                  style="Subheading.TLabel").pack(anchor=tk.W, pady=(2, 0))

        ttk.Separator(self, orient=tk.HORIZONTAL).grid(row=1, column=0,
                                                        sticky=tk.EW, padx=20, pady=(0, 8))

        # ── Directories ──
        dir_frame = ttk.LabelFrame(self, text="  Directories  ", padding=12)
        dir_frame.grid(row=2, column=0, sticky=tk.EW, **pad)
        dir_frame.columnconfigure(0, weight=1)

        self._input_dir = DirectoryEntry(dir_frame, "Source:", on_change=self._update_file_count)
        self._input_dir.grid(row=0, column=0, sticky=tk.EW, pady=(0, 6))

        self._output_dir = DirectoryEntry(dir_frame, "Output:")
        self._output_dir.grid(row=1, column=0, sticky=tk.EW)

        # ── File count indicator ──
        count_frame = ttk.Frame(self, style="Surface.TFrame")
        count_frame.grid(row=3, column=0, sticky=tk.EW, padx=20, pady=(4, 8))
        count_frame.columnconfigure(0, weight=1)
        inner_pad = ttk.Frame(count_frame, style="Surface.TFrame")
        inner_pad.pack(fill=tk.X, padx=12, pady=8)

        self._file_count_var = tk.StringVar(value="Select a source directory and file types")
        self._file_count_label = ttk.Label(inner_pad, textvariable=self._file_count_var,
                                           style="FileCount.TLabel")
        self._file_count_label.pack(anchor=tk.W)

        # ── Settings row: format + file types side by side ──
        settings_frame = ttk.Frame(self)
        settings_frame.grid(row=4, column=0, sticky=tk.EW, padx=20, pady=(0, 4))
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)

        # Date format
        fmt_frame = ttk.LabelFrame(settings_frame, text="  Date Format  ", padding=12)
        fmt_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 6))
        fmt_frame.columnconfigure(0, weight=1)

        fmt_row = ttk.Frame(fmt_frame)
        fmt_row.pack(fill=tk.X, pady=(0, 6))
        fmt_row.columnconfigure(0, weight=1)

        self._format_var = tk.StringVar(value="%Y/%m/%d")
        fmt_entry = ttk.Entry(fmt_row, textvariable=self._format_var, font=("Consolas", 11))
        fmt_entry.grid(row=0, column=0, sticky=tk.EW, padx=(0, 6))

        help_btn = ttk.Button(fmt_row, text="?", width=3, command=self._show_format_help)
        help_btn.grid(row=0, column=1)

        ttk.Label(fmt_frame, text=FORMAT_HINT, style="Help.TLabel").pack(anchor=tk.W)

        # File types
        types_frame = ttk.LabelFrame(settings_frame, text="  File Types  ", padding=12)
        types_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(6, 0))

        self._file_types = CheckbuttonGroup(types_frame, self._registry.get_all_extensions(),
                                            on_change=self._update_file_count)
        self._file_types.pack(anchor=tk.W)

        # ── Options ──
        opts_frame = ttk.LabelFrame(self, text="  Options  ", padding=12)
        opts_frame.grid(row=5, column=0, sticky=tk.EW, **pad)

        self._unknown_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="Move files with unknown dates to separate folder",
                        variable=self._unknown_var).pack(anchor=tk.W)

        # ── Actions ──
        action_frame = ttk.Frame(self)
        action_frame.grid(row=6, column=0, sticky=tk.EW, padx=20, pady=(12, 0))

        self._btn_copy = ttk.Button(action_frame, text="Copy Files",
                                    command=self._on_copy, style="TButton")
        self._btn_copy.pack(side=tk.RIGHT, padx=(8, 0))

        self._btn_move = ttk.Button(action_frame, text="Move Files",
                                    command=self._on_move, style="Action.TButton")
        self._btn_move.pack(side=tk.RIGHT)

        # ── Progress ──
        progress_frame = ttk.Frame(self)
        progress_frame.grid(row=7, column=0, sticky=tk.EW, padx=20, pady=(12, 0))
        progress_frame.grid_remove()
        progress_frame.columnconfigure(0, weight=1)
        self._progress_frame = progress_frame

        self._progress = ttk.Progressbar(progress_frame, mode="determinate", style="TProgressbar")
        self._progress.grid(row=0, column=0, sticky=tk.EW)

        self._progress_text = tk.Label(progress_frame, text="0/0",
                                       font=("Segoe UI Semibold", 9),
                                       fg=FG, bg=BG, anchor=tk.CENTER)
        self._progress_text.grid(row=0, column=0, sticky=tk.EW)

        self._processed_count = 0
        self._total_count = 0

        # ── Status bar ──
        status_frame = ttk.Frame(self, style="Surface.TFrame")
        status_frame.grid(row=8, column=0, sticky=tk.EW + tk.S, padx=0, pady=(12, 0))
        self.rowconfigure(8, weight=1)

        self._status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self._status_var,
                  style="Status.TLabel").pack(anchor=tk.W, padx=16, pady=6)

    # ── Format help window ─────────────────────────────────────

    def _show_format_help(self) -> None:
        win = tk.Toplevel(self)
        win.title("Date Format Reference")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        pad = ttk.Frame(win, padding=20)
        pad.pack(fill=tk.BOTH, expand=True)

        ttk.Label(pad, text="Date Format Codes", style="Heading.TLabel").pack(anchor=tk.W)
        ttk.Label(pad, text="Use these codes in the format field. Slashes create subfolders.",
                  style="Subheading.TLabel").pack(anchor=tk.W, pady=(2, 12))

        for section_name, codes in FORMAT_REFERENCE:
            ttk.Label(pad, text=section_name,
                      font=("Segoe UI Semibold", 10), foreground=FG_HEADING,
                      background=BG).pack(anchor=tk.W, pady=(8, 4))

            table = ttk.Frame(pad)
            table.pack(fill=tk.X, pady=(0, 4))
            table.columnconfigure(1, weight=1)

            for i, (code, desc, example) in enumerate(codes):
                bg = BG_SURFACE if i % 2 == 0 else BG
                row = tk.Frame(table, bg=bg)
                row.grid(row=i, column=0, columnspan=3, sticky=tk.EW)
                table.columnconfigure(0, weight=0)

                tk.Label(row, text=code, font=("Consolas", 10, "bold"),
                         fg=ACCENT, bg=bg, width=6, anchor=tk.W).pack(
                    side=tk.LEFT, padx=(8, 12), pady=3)
                tk.Label(row, text=desc, font=("Segoe UI", 9),
                         fg=FG, bg=bg, anchor=tk.W).pack(
                    side=tk.LEFT, padx=(0, 16), pady=3, expand=True, fill=tk.X)
                tk.Label(row, text=example, font=("Consolas", 9),
                         fg=FG_DIM, bg=bg, anchor=tk.E).pack(
                    side=tk.RIGHT, padx=(0, 8), pady=3)

        ttk.Separator(pad, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(12, 8))

        tip = ttk.Label(pad, style="Help.TLabel", justify=tk.LEFT,
                        text="Tip:  %d = day,  %D = month/day/year (with slashes!)\n"
                             "       %m = month,  %M = minute  \u2014  case matters!")
        tip.pack(anchor=tk.W)

        ttk.Button(pad, text="Close", command=win.destroy,
                   style="TButton").pack(anchor=tk.E, pady=(12, 0))

        # Center on parent
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - win.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

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

        self._processed_count = 0
        self._total_count = 0
        self._progress["value"] = 0
        self._progress_text.config(text="0/0")
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
        self._progress["maximum"] = total
        self._progress_text.config(text=f"0/{total}")

    def _on_progress(self, result: FileResult) -> None:
        self._processed_count += 1
        self._progress["value"] = self._processed_count
        self._progress_text.config(text=f"{self._processed_count}/{self._total_count}")
        self._status_var.set(f"Processing: {result.source.name} \u2014 {result.status}")

    def _on_complete(self, results: list[FileResult]) -> None:
        self._processing = False
        self._btn_move.config(state=tk.NORMAL)
        self._btn_copy.config(state=tk.NORMAL)
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
        if self._processing:
            messagebox.showwarning("Warning", "Processing is still running.")
            return
        self._save_config()
        self.destroy()
