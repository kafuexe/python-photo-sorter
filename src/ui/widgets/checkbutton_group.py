import tkinter as tk


class CheckbuttonGroup(tk.Frame):
    """Dynamic checkbutton group built from a set of extensions."""

    def __init__(self, parent, extensions: set[str], **kwargs):
        super().__init__(parent, **kwargs)

        self._vars: dict[str, tk.BooleanVar] = {}

        for ext in sorted(extensions):
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(self, text=ext, variable=var)
            cb.pack(side=tk.LEFT, padx=4)
            self._vars[ext] = var

    def get_selected(self) -> list[str]:
        return [ext for ext, var in self._vars.items() if var.get()]

    def set_selected(self, extensions: list[str]) -> None:
        ext_set = {e.lower() for e in extensions}
        for ext, var in self._vars.items():
            var.set(ext.lower() in ext_set)
