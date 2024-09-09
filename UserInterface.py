import tkinter as tk
from tkinter import filedialog

# need to read exif and xmp for matadeta?


SUPPORTED_FILE_TYPES = {"png", "jpg", "mpeg", "mpg", "avi"}


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self.geometry("900x640")
        self.title("CyberChaperone")

        # input section ----------------------------------------------------------
        self.button_change_input_dir = tk.Button(
            self,
            text="Browse Files",
            command=lambda: self.BrowseFiles(self.textbox_input_dir),
        )
        self.textbox_input_dir = tk.Entry(self, width=50, bg="light yellow")

        # output section --------------------------------------------------------
        self.button_change_output_dir = tk.Button(
            self,
            text="Browse Files",
            command=lambda: self.BrowseFiles(self.textbox_output_dir),
        )
        self.textbox_output_dir = tk.Entry(self, width=50, bg="light yellow")

        # other ----------------------------------------------------------------
        self.button_exit = tk.Button(self, text="Exit", command=exit)

        self.textbox_input_dir.grid(row=1, column=1)
        self.button_change_input_dir.grid(row=1, column=2)

        self.textbox_output_dir.grid(row=2, column=1)
        self.button_change_output_dir.grid(row=2, column=2)

        self.button_exit.grid(column=1, row=3)
        self.mainloop()

    def BrowseFiles(self, textbox):
        filename = filedialog.askdirectory(
            initialdir="/",
            title="Select a folder",
        )
        # Change label contents
        print(f"Selected {filename} as input directory")
        textbox.delete(0, "end")
        textbox.insert(0, filename)


x = App()
