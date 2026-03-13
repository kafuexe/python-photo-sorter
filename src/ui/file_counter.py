import threading
import tkinter as tk
from pathlib import Path


class FileCounter:
    """Debounced, background-threaded file counter for a tkinter app."""

    _FILE_COUNT_LIMIT = 25_000

    def __init__(self, window: tk.Misc, file_count_var: tk.StringVar,
                 status_var: tk.StringVar,
                 get_input_dir, get_extensions, is_processing):
        self._window = window
        self._file_count_var = file_count_var
        self._status_var = status_var
        self._get_input_dir = get_input_dir
        self._get_extensions = get_extensions
        self._is_processing = is_processing
        self._after_id = None
        self._generation = 0

    def schedule(self) -> None:
        if self._is_processing():
            return
        if self._after_id is not None:
            self._window.after_cancel(self._after_id)
        self._after_id = self._window.after(300, self._run)

    def _run(self) -> None:
        self._after_id = None

        input_dir = self._get_input_dir()
        extensions = self._get_extensions()

        if not input_dir or not Path(input_dir).is_dir() or not extensions:
            self._file_count_var.set("Select a source directory and file types")
            self._status_var.set("Ready")
            return

        ext_set = {f".{e.lower().lstrip('.')}" for e in extensions}
        self._generation += 1
        gen = self._generation
        self._file_count_var.set("Scanning...")
        threading.Thread(target=self._count, args=(input_dir, ext_set, gen), daemon=True).start()

    def _count(self, input_dir: str, ext_set: set, generation: int) -> None:
        count = 0
        for f in Path(input_dir).rglob("*"):
            if generation != self._generation:
                return
            if f.is_file() and f.suffix.lower() in ext_set:
                count += 1
                if count >= self._FILE_COUNT_LIMIT:
                    self._window.after(0, self._done, count, generation)
                    return
        self._window.after(0, self._done, count, generation)

    def _done(self, count: int, generation: int) -> None:
        if generation != self._generation:
            return
        if count >= self._FILE_COUNT_LIMIT:
            self._file_count_var.set(f"Found {count:,}+ files")
        else:
            self._file_count_var.set(f"Found {count} file{'s' if count != 1 else ''}")
        self._status_var.set("Ready")
