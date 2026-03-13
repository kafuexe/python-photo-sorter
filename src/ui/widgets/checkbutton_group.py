import tkinter as tk
from tkinter import ttk


class CheckbuttonGroup(ttk.Frame):
    """Dynamic checkbutton group built from a set of extensions."""

    def __init__(self, parent, extensions: set[str], on_change=None, **kwargs):
        super().__init__(parent, **kwargs)

        self._vars: dict[str, tk.BooleanVar] = {}

        for i, ext in enumerate(sorted(extensions)):
            var = tk.BooleanVar(value=False)
            if on_change:
                var.trace_add("write", lambda *_: on_change())
            cb = ttk.Checkbutton(self, text=f".{ext}", variable=var)
            cb.grid(row=0, column=i, padx=(0, 12), sticky=tk.W)
            self._vars[ext] = var

    def get_selected(self) -> list[str]:
        return [ext for ext, var in self._vars.items() if var.get()]

    def set_selected(self, extensions: list[str]) -> None:
        ext_set = {e.lower() for e in extensions}
        for ext, var in self._vars.items():
            var.set(ext.lower() in ext_set)
