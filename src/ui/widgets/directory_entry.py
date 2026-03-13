import tkinter as tk
from tkinter import ttk, filedialog


class DirectoryEntry(ttk.Frame):
    """Reusable widget: label + text entry + browse button using grid layout."""

    def __init__(self, parent, label_text: str, on_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_change = on_change

        self.columnconfigure(1, weight=1)

        self._label = ttk.Label(self, text=label_text, width=8, anchor=tk.E)
        self._label.grid(row=0, column=0, padx=(0, 8), sticky=tk.E)

        self._var = tk.StringVar()
        self._entry = ttk.Entry(self, textvariable=self._var, font=("Segoe UI", 11))
        self._entry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 8))

        self._button = ttk.Button(self, text="Browse...", command=self._browse, width=10)
        self._button.grid(row=0, column=2)

        if self._on_change:
            self._var.trace_add("write", lambda *_: self._on_change())

    def _browse(self) -> None:
        path = filedialog.askdirectory(initialdir="/", title="Select a folder")
        if path:
            self._var.set(path)

    def get(self) -> str:
        return self._var.get()

    def set(self, path: str) -> None:
        self._var.set(path)
