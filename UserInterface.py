import tkinter as tk
from tkinter import filedialog


class App(tk.Tk):
    def __init__(self, support_file_types):
        tk.Tk.__init__(self)

        self.used_file_types = []
        SUPPORTED_FILE_TYPES = support_file_types
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

        # filetypes Check buttons -------------------------------------------------
        label_row = 0
        self.Checkbutton_list = []
        for filetype in SUPPORTED_FILE_TYPES:
            self.Checkbutton_list.append(
                tk.Checkbutton(
                    text=filetype,
                    command=lambda filetype=filetype: self.AddRemoveFileType(filetype),
                )
            )

        for i in range(len(self.Checkbutton_list)):
            self.Checkbutton_list[i].grid(column=6, row=i, sticky="w")

        # other ----------------------------------------------------------------
        self.button_exit = tk.Button(self, text="Exit", command=exit)

        self.textbox_input_dir.grid(row=1, column=1)
        self.button_change_input_dir.grid(row=1, column=2)

        self.textbox_output_dir.grid(row=2, column=1)
        self.button_change_output_dir.grid(row=2, column=2)

        self.button_exit.grid(column=1, row=3)
        self.mainloop()

    def AddRemoveFileType(self, fileType):
        if fileType not in SUPPORTED_FILE_TYPES:
            return

        if fileType in self.used_file_types:
            self.used_file_types.remove(fileType)
        else:
            self.used_file_types.append(fileType)
        print(self.used_file_types)

    def BrowseFiles(self, textbox):
        filename = filedialog.askdirectory(
            initial_dir="/",
            title="Select a folder",
        )
        # Change label contents
        print(f"Selected {filename} as input directory")
        textbox.delete(0, "end")
        textbox.insert(0, filename)


if __name__ == "__main__":
    pass
