import tkinter as tk
from tkinter import filedialog


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self.geometry("900x640")
        self.title("CyberChaperone")

        self.button_change_input_dir = tk.Button(
            self, text="Browse Files", command=self.change_input_dir
        )

        self.button_exit = tk.Button(self, text="Exit", command=exit)

        self.textbox_input_dir = tk.Entry(self, width=50, bg="light yellow")

        self.textbox_input_dir.grid(row=1, column=1)
        self.button_change_input_dir.grid(column=1, row=2)
        self.button_exit.grid(column=1, row=3)
        self.mainloop()

    def change_input_dir(self):
        filename = filedialog.askdirectory(
            initialdir="/",
            title="Select a folder",
        )

        # Change label contents
        print(f"Selected {filename} as input directory")
        self.textbox_input_dir.delete(0, "end")
        self.textbox_input_dir.insert(0, filename)


x = App()
