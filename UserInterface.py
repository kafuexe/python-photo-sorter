import tkinter as tk
from tkinter import filedialog
import os
from tkinter.ttk import Progressbar
import time, threading

from MetaDataRead import MetaDataReader


class App(tk.Tk):
    def __init__(self, support_file_types):
        tk.Tk.__init__(self)
        global SUPPORTED_FILE_TYPES
        SUPPORTED_FILE_TYPES = support_file_types
        self.mtdr = MetaDataReader(SUPPORTED_FILE_TYPES)

        self.used_file_types = []

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
        for pos in range(len(SUPPORTED_FILE_TYPES)):
            filetype = SUPPORTED_FILE_TYPES[pos]
            x = tk.Checkbutton(
                text=filetype,
                command=lambda filetype=filetype: self.AddRemoveFileType(filetype),
            )

            self.Checkbutton_list.append(x)

            x.grid(column=7, row=pos, sticky="w")

        for i in range(len(self.Checkbutton_list)):
            pass

        # other ----------------------------------------------------------------
        self.button_exit = tk.Button(self, text="Exit", command=exit)
        self.button_move = tk.Button(self, text="Move", command=self.move)

        self.textbox_input_dir.grid(row=1, column=1)
        self.button_change_input_dir.grid(row=1, column=2)

        self.textbox_output_dir.grid(row=2, column=1)
        self.button_change_output_dir.grid(row=2, column=2)

        self.button_move.grid(column=1, row=3)
        self.button_exit.grid(column=1, row=4)
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
            # initialdir="/",
            initialdir="D:\\.backups\\phone backups\\pixel7ofek20230126\\DCIM\\Camera\\",
            title="Select a folder",
        )
        # Change label contents
        print(f"Selected {filename} as input directory")
        textbox.delete(0, "end")
        textbox.insert(0, filename)

    def throw_error_message(self, message):
        tk.messagebox.showerror(title="Error", message=message)

    def my_progressbar(self):
        root = tk.Tk()
        root.geometry("400x50")
        pb = Progressbar(
            root, length=100, mode="determinate", maximum=100, takefocus=True
        )
        pb["value"] = 0
        pb.grid(row=1, column=1)
        return root, pb

    def move(self):
        response = tk.messagebox.askyesno(
            title="Are you Sure?",
            message="""one last time before moving files, make sure all
            settings are correct, if you are sure click yes""",
            default="no",
        )
        if not response:
            return

        folder = os.path.join(self.textbox_input_dir.get(), "")

        lstdirlen = len(os.listdir(folder))

        files_compleated = 0
        pbroot, pb = self.my_progressbar()
        pb["value"] = 0

        for filename in os.listdir(folder):
            data = None
            if filename.endswith(tuple(self.used_file_types)):
                img_path = os.path.join(folder, filename)
                if os.path.isfile(img_path):
                    match filename.split(".")[-1]:
                        case "jpg" | "png" | "wepg":
                            data = self.mtdr.imgDateExif(img_path)
                        case "mov" | "avi" | "mp4":
                            data = self.mtdr.DateExifTool(img_path)
                        case _:
                            data = None
            print(f"{filename} ||| {data}")

            ## progress bar updating
            files_compleated += 1
            pb["value"] = (files_compleated / lstdirlen) * 100
            pbroot.update()

        pbroot.destroy()


if __name__ == "__main__":
    pass
