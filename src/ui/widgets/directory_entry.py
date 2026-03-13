import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

from ..theme import BG, BG_INPUT, FG, FG_DIM, ACCENT, BORDER


class DirectoryEntry(ctk.CTkFrame):
    """Reusable widget: label + text entry + browse button."""

    def __init__(self, parent, label_text: str, on_change=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_change = on_change

        self.grid_columnconfigure(1, weight=1)

        self._label = ctk.CTkLabel(self, text=label_text, width=60, anchor=tk.E,
                                   font=ctk.CTkFont(size=13))
        self._label.grid(row=0, column=0, padx=(0, 8), sticky=tk.E)

        self._var = tk.StringVar()
        self._entry = ctk.CTkEntry(self, textvariable=self._var,
                                   font=ctk.CTkFont(size=13),
                                   fg_color=BG_INPUT, border_color=BORDER,
                                   text_color=FG)
        self._entry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 8))

        self._button = ctk.CTkButton(self, text="Browse...", command=self._browse,
                                     width=90, fg_color=BG_INPUT, hover_color=BORDER,
                                     text_color=FG, border_width=1, border_color=BORDER)
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
