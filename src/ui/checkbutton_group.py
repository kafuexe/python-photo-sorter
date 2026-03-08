"""Checkbutton group for file type selection."""
import tkinter as tk


class CheckbuttonGroup:
    """A group of checkbuttons for file type selection."""

    def __init__(self, parent: tk.Widget, file_types: list[str]):
        """Create checkbutton group.

        Args:
            parent: Parent widget.
            file_types: List of file extensions to show as checkbuttons.
        """
        self.checkbuttons = []
        for pos, filetype in enumerate(file_types):
            cb = tk.Checkbutton(parent, text=filetype)
            cb.grid(column=10, row=pos, sticky="w")
            self.checkbuttons.append(cb)

    def select(self, extensions: list[str]) -> None:
        """Select checkbuttons by extension.

        Args:
            extensions: List of file extensions to select.
        """
        for cb, ext in zip(self.checkbuttons, extensions):
            if cb.cget("text").lower() == ext.lower():
                cb.select()

    def get_selected(self) -> list[str]:
        """Get list of selected file types.

        Returns:
            List of selected file type strings.
        """
        return [cb.cget("text") for cb in self.checkbuttons if cb.selected]
