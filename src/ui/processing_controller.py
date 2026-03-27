import logging
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from ..models.file_result import FileResult
from ..models.processing_config import ProcessingConfig
from ..services.log_service import LogService
from ..services.processing_service import ProcessingService

logger = logging.getLogger(__name__)


class ProcessingController:
    """Handles validation, threaded processing, progress updates, and completion."""

    def __init__(self, window: tk.Misc,
                 processing_service: ProcessingService,
                 log_service: LogService,
                 get_input_dir, get_output_dir, get_extensions,
                 get_format, get_unknown,
                 btn_move: ctk.CTkButton, btn_copy: ctk.CTkButton,
                 progress_frame: ctk.CTkFrame, progress_bar: ctk.CTkProgressBar,
                 progress_label: ctk.CTkLabel, timing_label: ctk.CTkLabel,
                 breakdown_label: ctk.CTkLabel, current_file_label: ctk.CTkLabel,
                 status_var: tk.StringVar):
        self._window = window
        self._processing_service = processing_service
        self._log_service = log_service
        self._get_input_dir = get_input_dir
        self._get_output_dir = get_output_dir
        self._get_extensions = get_extensions
        self._get_format = get_format
        self._get_unknown = get_unknown
        self._btn_move = btn_move
        self._btn_copy = btn_copy
        self._progress_frame = progress_frame
        self._progress_bar = progress_bar
        self._progress_label = progress_label
        self._timing_label = timing_label
        self._breakdown_label = breakdown_label
        self._current_file_label = current_file_label
        self._status_var = status_var
        self._processing = False
        self._processed_count = 0
        self._total_count = 0
        self._start_time: float = 0.0
        self._success_count = 0
        self._unknown_count = 0
        self._skipped_count = 0
        self._error_count = 0

    @property
    def is_processing(self) -> bool:
        return self._processing

    def start(self, action: str) -> None:
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
        self._success_count = 0
        self._unknown_count = 0
        self._skipped_count = 0
        self._error_count = 0
        self._start_time = time.perf_counter()
        self._progress_bar.set(0)
        self._progress_label.configure(text="0/0")
        self._timing_label.configure(text="0.0s elapsed")
        self._breakdown_label.configure(text="\u2713 0 sorted  \u2b21 0 unknown  \u2298 0 skipped  \u2717 0 errors")
        self._current_file_label.configure(text="")
        self._progress_frame.grid()
        logger.info("Starting %s operation", action)

        self._current_config = self._build_config(action)
        threading.Thread(
            target=self._run,
            args=(self._current_config,),
            daemon=True,
        ).start()

    def _validate(self) -> bool:
        input_dir = self._get_input_dir()
        output_dir = self._get_output_dir()

        if not input_dir or not output_dir:
            messagebox.showerror("Error", "Select input and output directories.")
            return False
        if not Path(input_dir).is_dir():
            messagebox.showerror("Error", "Input directory does not exist.")
            return False
        if not self._get_extensions():
            messagebox.showerror("Error", "Select at least one file type.")
            return False
        return True

    def _build_config(self, action: str) -> ProcessingConfig:
        return ProcessingConfig(
            input_dir=Path(self._get_input_dir()),
            output_dir=Path(self._get_output_dir()),
            date_format=self._get_format(),
            action=action,
            selected_extensions=self._get_extensions(),
            handle_unknown=self._get_unknown(),
        )

    def _run(self, config: ProcessingConfig) -> None:
        try:
            log_path = self._log_service.begin(config)
        except Exception as e:
            logger.error("Failed to open log file: %s", e)
            log_path = None

        def on_progress(result: FileResult) -> None:
            if log_path is not None:
                try:
                    self._log_service.log_result(result)
                except Exception as e:
                    logger.error("Failed to write log entry: %s", e)
            self._window.after(0, self._on_progress, result)

        def on_total(total: int) -> None:
            self._window.after(0, self._on_total, total)

        results, stats = self._processing_service.process(config, on_progress=on_progress,
                                                          on_total=on_total)

        if log_path is not None:
            try:
                self._log_service.finish(results, stats)
            except Exception as e:
                logger.error("Failed to finalize log: %s", e)

        self._window.after(0, self._on_complete, results, stats, log_path)

    def _on_total(self, total: int) -> None:
        self._total_count = total
        self._progress_label.configure(text=f"0/{total}")

    def _on_progress(self, result: FileResult) -> None:
        self._processed_count += 1

        # Update status counters
        if result.status == "success":
            self._success_count += 1
        elif result.status == "unknown":
            self._unknown_count += 1
        elif result.status == "skipped":
            self._skipped_count += 1
        elif result.status == "error":
            self._error_count += 1

        # Progress bar and count
        if self._total_count > 0:
            self._progress_bar.set(self._processed_count / self._total_count)
        self._progress_label.configure(text=f"{self._processed_count}/{self._total_count}")

        # Timing calculations
        elapsed = time.perf_counter() - self._start_time
        throughput = self._processed_count / elapsed if elapsed > 0 else 0.0
        remaining = self._total_count - self._processed_count
        eta = (elapsed / self._processed_count) * remaining if self._processed_count > 0 else 0.0
        self._timing_label.configure(
            text=f"{elapsed:.1f}s elapsed \u2014 ~{eta:.1f}s remaining \u2014 {throughput:.1f} files/sec"
        )

        # Status breakdown
        self._breakdown_label.configure(
            text=f"\u2713 {self._success_count} sorted  \u2b21 {self._unknown_count} unknown  \u2298 {self._skipped_count} skipped  \u2717 {self._error_count} errors"
        )

        # Current file line
        if result.destination:
            dest_display = str(result.destination)
        else:
            dest_display = result.status
        self._current_file_label.configure(
            text=f"Processing: {result.source.name} \u2192 {dest_display}"
        )

        self._status_var.set(f"Processing: {result.source.name} \u2014 {result.status}")

    def _on_complete(self, results: list[FileResult], stats, log_path) -> None:
        self._processing = False
        self._btn_move.configure(state=tk.NORMAL)
        self._btn_copy.configure(state=tk.NORMAL)
        self._progress_frame.grid_remove()

        success = sum(1 for r in results if r.status == "success")
        unknown = sum(1 for r in results if r.status == "unknown")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")

        summary = f"Done! {success} sorted, {unknown} unknown, {skipped} skipped, {errors} errors. ({stats.total:.1f}s)"
        self._status_var.set(summary)
        logger.info(summary)

        if log_path is not None:
            summary += f"\n\nLog saved to:\n{log_path}"

        messagebox.showinfo("Complete", summary)
