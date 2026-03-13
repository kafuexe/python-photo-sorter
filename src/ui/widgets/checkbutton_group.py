import tkinter as tk
import customtkinter as ctk

from ..theme import BG, ACCENT, BORDER, FG, FG_DIM


class CheckbuttonGroup(ctk.CTkFrame):
    """Dynamic checkbox group that wraps to multiple rows."""

    def __init__(self, parent, extensions: set[str], on_change=None, columns=4, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._on_change = on_change
        self._updating = False
        self._vars: dict[str, tk.BooleanVar] = {}

        # "All" toggle on its own row
        self._all_var = tk.BooleanVar(value=False)
        self._all_cb = ctk.CTkCheckBox(self, text="All", variable=self._all_var,
                                       command=self._on_all_toggled,
                                       fg_color=ACCENT, hover_color=ACCENT,
                                       text_color=FG)
        self._all_cb.grid(row=0, column=0, padx=(0, 12), pady=(0, 4), sticky=tk.W)

        sep = ctk.CTkFrame(self, height=1, fg_color=BORDER)
        sep.grid(row=1, column=0, columnspan=columns, sticky=tk.EW, pady=(0, 6))

        # Individual extension checkboxes in a grid
        for i, ext in enumerate(sorted(extensions)):
            var = tk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(self, text=f".{ext}", variable=var,
                                 command=self._on_item_toggled,
                                 fg_color=ACCENT, hover_color=ACCENT,
                                 text_color=FG)
            row = (i // columns) + 2
            col = i % columns
            cb.grid(row=row, column=col, padx=(0, 12), pady=2, sticky=tk.W)
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
