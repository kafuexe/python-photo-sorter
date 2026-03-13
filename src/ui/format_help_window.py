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


def show_format_help(parent) -> None:
    """Open the date format reference window."""
    win = ctk.CTkToplevel(parent)
    win.title("Date Format Reference")
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    pad = ctk.CTkFrame(win, fg_color=BG)
    pad.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    ctk.CTkLabel(pad, text="Date Format Codes",
                 font=ctk.CTkFont(size=18, weight="bold"),
                 text_color=FG_HEADING).pack(anchor=tk.W)
    ctk.CTkLabel(pad, text="Use these codes in the format field. Slashes create subfolders.",
                 font=ctk.CTkFont(size=12),
                 text_color=FG_DIM).pack(anchor=tk.W, pady=(2, 12))

    for section_name, codes in FORMAT_REFERENCE:
        ctk.CTkLabel(pad, text=section_name,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=FG_HEADING).pack(anchor=tk.W, pady=(8, 4))

        table = ctk.CTkFrame(pad, fg_color="transparent")
        table.pack(fill=tk.X, pady=(0, 4))
        table.grid_columnconfigure(1, weight=1)

        for i, (code, desc, example) in enumerate(codes):
            row_bg = BG_SURFACE if i % 2 == 0 else BG
            row = ctk.CTkFrame(table, fg_color=row_bg, corner_radius=0)
            row.grid(row=i, column=0, columnspan=3, sticky=tk.EW)
            table.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row, text=code, font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                         text_color=ACCENT, width=50, anchor=tk.W).pack(
                side=tk.LEFT, padx=(8, 12), pady=3)
            ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=12),
                         text_color=FG, anchor=tk.W).pack(
                side=tk.LEFT, padx=(0, 16), pady=3, expand=True, fill=tk.X)
            ctk.CTkLabel(row, text=example, font=ctk.CTkFont(family="Consolas", size=12),
                         text_color=FG_DIM, anchor=tk.E).pack(
                side=tk.RIGHT, padx=(0, 8), pady=3)

    sep = ctk.CTkFrame(pad, height=1, fg_color=BORDER)
    sep.pack(fill=tk.X, pady=(12, 8))

    ctk.CTkLabel(pad, font=ctk.CTkFont(family="Consolas", size=11),
                 text_color=FG_DIM, justify=tk.LEFT,
                 text="Tip:  %d = day,  %D = month/day/year (with slashes!)\n"
                      "       %m = month,  %M = minute  \u2014  case matters!").pack(anchor=tk.W)

    ctk.CTkButton(pad, text="Close", command=win.destroy,
                  fg_color=BG_SURFACE, hover_color=BORDER,
                  text_color=FG, border_width=1, border_color=BORDER,
                  width=80).pack(anchor=tk.E, pady=(12, 0))

    # Center on parent
    win.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - win.winfo_width()) // 2
    y = parent.winfo_y() + (parent.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{x}+{y}")
