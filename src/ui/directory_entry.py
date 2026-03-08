"""Directory entry widget with browse button."""
import tkinter as tk
from tkinter import filedialog


class DirectoryEntry:
    """A directory entry widget with browse button."""

    def __init__(self, parent: tk.Widget, text: str, width: int = 40, initial_text: str = ""):
        """Create directory entry.

        Args:
            parent: Parent widget.
            text: Label text for the entry.
            width: Entry field width.
            initial_text: Initial text value.
        """
        self.entry_var = tk.StringVar(value=initial_text)
        self.entry = tk.Entry(parent, textvariable=self.entry_var, width=width, bg="light yellow")
        self.browse_btn = tk.Button(parent, text="Browse", command=self.browse)

    def browse(self) -> None:
        """Open directory browser dialog."""
        filename = filedialog.askdirectory(initialdir="/", title="Select a folder")
        if filename:
            self.entry_var.set(filename)

    def get(self) -> str:
        """Get current value."""
        return self.entry_var.get()

    def set(self, value: str) -> None:
        """Set value."""
        self.entry_var.set(value)

    def destroy(self) -> None:
        """Destroy the widget."""
        self.entry.destroy()
        self.browse_btn.destroy()
