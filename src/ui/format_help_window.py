import tkinter as tk
import customtkinter as ctk

from .theme import BG, BG_SURFACE, FG, FG_DIM, FG_HEADING, ACCENT, BORDER

FORMAT_REFERENCE = [
    ("Common codes", [
        ("%d", "Day of month", "01\u201331"),
        ("%m", "Month number", "01\u201312"),
        ("%y", "Year (short)", "24"),
        ("%Y", "Year (full)", "2024"),
        ("%H", "Hour (24h)", "00\u201323"),
        ("%I", "Hour (12h)", "01\u201312"),
        ("%M", "Minute", "00\u201359"),
        ("%S", "Second", "00\u201359"),
        ("%p", "AM / PM", "PM"),
    ]),
    ("Names", [
        ("%a", "Weekday (short)", "Wed"),
        ("%A", "Weekday (full)", "Wednesday"),
        ("%b", "Month (short)", "Dec"),
        ("%B", "Month (full)", "December"),
    ]),
    ("Other", [
        ("%j", "Day of year", "001\u2013366"),
        ("%U", "Week number (Sun)", "00\u201353"),
        ("%W", "Week number (Mon)", "00\u201353"),
        ("%f", "Microsecond", "000000\u2013999999"),
        ("%z", "UTC offset", "+0100"),
        ("%Z", "Timezone", "CST"),
        ("%%", "Literal %", "%"),
    ]),
]

MAX_WIDTH = 520
MAX_HEIGHT = 600


def show_format_help(parent) -> None:
    """Open the date format reference window."""
    win = ctk.CTkToplevel(parent)
    win.title("Date Format Reference")
    win.resizable(True, True)
    win.transient(parent)
    win.grab_set()
    win.maxsize(MAX_WIDTH, MAX_HEIGHT)

    # Scrollable content area
    scroll = ctk.CTkScrollableFrame(win, fg_color=BG, width=MAX_WIDTH - 40,
                                    scrollbar_button_color=BORDER,
                                    scrollbar_button_hover_color=FG_DIM)
    scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

    ctk.CTkLabel(scroll, text="Date Format Codes",
                 font=ctk.CTkFont(size=18, weight="bold"),
                 text_color=FG_HEADING).pack(anchor=tk.W)
    ctk.CTkLabel(scroll, text="Use these codes in the format field. Slashes create subfolders.",
                 font=ctk.CTkFont(size=12),
                 text_color=FG_DIM).pack(anchor=tk.W, pady=(2, 12))

    for section_name, codes in FORMAT_REFERENCE:
        ctk.CTkLabel(scroll, text=section_name,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=FG_HEADING).pack(anchor=tk.W, pady=(8, 4))

        table = ctk.CTkFrame(scroll, fg_color="transparent")
        table.pack(fill=tk.X, pady=(0, 4))
        table.grid_columnconfigure(0, weight=1)

        for i, (code, desc, example) in enumerate(codes):
            row_bg = BG_SURFACE if i % 2 == 0 else BG
            row = ctk.CTkFrame(table, fg_color=row_bg, corner_radius=0)
            row.grid(row=i, column=0, columnspan=3, sticky=tk.EW)

            ctk.CTkLabel(row, text=code, font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                         text_color=ACCENT, width=50, anchor=tk.W).pack(
                side=tk.LEFT, padx=(8, 12), pady=3)
            ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=12),
                         text_color=FG, anchor=tk.W).pack(
                side=tk.LEFT, padx=(0, 16), pady=3, expand=True, fill=tk.X)
            ctk.CTkLabel(row, text=example, font=ctk.CTkFont(family="Consolas", size=12),
                         text_color=FG_DIM, anchor=tk.E).pack(
                side=tk.RIGHT, padx=(0, 8), pady=3)

    sep = ctk.CTkFrame(scroll, height=1, fg_color=BORDER)
    sep.pack(fill=tk.X, pady=(12, 8))

    ctk.CTkLabel(scroll, font=ctk.CTkFont(family="Consolas", size=11),
                 text_color=FG_DIM, justify=tk.LEFT,
                 text="Tip:  %d = day,  %D = month/day/year (with slashes!)\n"
                      "       %m = month,  %M = minute  \u2014  case matters!").pack(anchor=tk.W)

    # Close button outside scroll area so it's always visible
    ctk.CTkButton(win, text="Close", command=win.destroy,
                  fg_color=BG_SURFACE, hover_color=BORDER,
                  text_color=FG, border_width=1, border_color=BORDER,
                  width=80).pack(anchor=tk.E, padx=10, pady=10)

    # Set initial size and center on parent
    w, h = MAX_WIDTH, MAX_HEIGHT
    x = parent.winfo_x() + (parent.winfo_width() - w) // 2
    y = parent.winfo_y() + (parent.winfo_height() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")
