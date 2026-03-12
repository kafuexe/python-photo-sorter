import tkinter as tk
from tkinter import filedialog


class DirectoryEntry(tk.Frame):
    """Reusable widget: label + text entry + browse button."""

    def __init__(self, parent, label_text: str, **kwargs):
        super().__init__(parent, **kwargs)

        self._label = tk.Label(self, text=label_text)
        self._label.pack(side=tk.LEFT, padx=(0, 5))

        self._var = tk.StringVar()
        self._entry = tk.Entry(self, textvariable=self._var, width=40, bg="light yellow")
        self._entry.pack(side=tk.LEFT, padx=(0, 5))

        self._button = tk.Button(self, text="Browse", command=self._browse)
        self._button.pack(side=tk.LEFT)

    def _browse(self) -> None:
        path = filedialog.askdirectory(initialdir="/", title="Select a folder")
        if path:
            self._var.set(path)

    def get(self) -> str:
        return self._var.get()

    def set(self, path: str) -> None:
        self._var.set(path)
