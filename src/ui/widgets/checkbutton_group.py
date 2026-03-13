import tkinter as tk
from tkinter import ttk


class CheckbuttonGroup(ttk.Frame):
    """Dynamic checkbutton group built from a set of extensions."""

    def __init__(self, parent, extensions: set[str], on_change=None, **kwargs):
        super().__init__(parent, **kwargs)

        self._on_change = on_change
        self._updating = False
        self._vars: dict[str, tk.BooleanVar] = {}

        # "All" toggle
        self._all_var = tk.BooleanVar(value=False)
        self._all_var.trace_add("write", lambda *_: self._on_all_toggled())
        all_cb = ttk.Checkbutton(self, text="All", variable=self._all_var)
        all_cb.grid(row=0, column=0, padx=(0, 16), sticky=tk.W)

        ttk.Separator(self, orient=tk.VERTICAL).grid(row=0, column=1, sticky=tk.NS, padx=(0, 12))

        # Individual extension checkbuttons
        for i, ext in enumerate(sorted(extensions)):
            var = tk.BooleanVar(value=False)
            var.trace_add("write", lambda *_: self._on_item_toggled())
            cb = ttk.Checkbutton(self, text=f".{ext}", variable=var)
            cb.grid(row=0, column=i + 2, padx=(0, 12), sticky=tk.W)
            self._vars[ext] = var

    def _on_all_toggled(self) -> None:
        if self._updating:
            return
        self._updating = True
        select = self._all_var.get()
        for var in self._vars.values():
            var.set(select)
        self._updating = False
        if self._on_change:
            self._on_change()

    def _on_item_toggled(self) -> None:
        if self._updating:
            return
        self._updating = True
        all_checked = all(var.get() for var in self._vars.values())
        self._all_var.set(all_checked)
        self._updating = False
        if self._on_change:
            self._on_change()

    def get_selected(self) -> list[str]:
        return [ext for ext, var in self._vars.items() if var.get()]

    def set_selected(self, extensions: list[str]) -> None:
        self._updating = True
        ext_set = {e.lower() for e in extensions}
        for ext, var in self._vars.items():
            var.set(ext.lower() in ext_set)
        self._all_var.set(all(var.get() for var in self._vars.values()))
        self._updating = False
