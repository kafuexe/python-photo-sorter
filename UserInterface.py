import tkinter as tk
from tkinter import filedialog
import os
from tkinter.ttk import Progressbar
import time, threading
from datetime import datetime
import datetime as Dt
from MetaDataRead import MetaDataReader
import configparser
from idlelib.tooltip import Hovertip

TOOLTIPTEXT = """
Form  	|Description					|Example			
%a	|Weekday, short version				|Wed 			
%A	|Weekday, full version				|Wednesday		
%w	|Weekday as a number 0-6, 0 is Sunday		|3			
%d	|Day of month 01-31				|31			
%b	|Month name, short version			|Dec			
%B	|Month name, full version			    |December		
%m	|Month as a number 01-12			    |12			
%y	|Year, short version, without century		    |18			
%Y	|Year, full version				    |2018			
%H	|Hour 00-23					|17			
%I	|Hour 00-12					|05			
%p	|AM/PM						|PM			
%M	|Minute 00-59					|41			
%S	|Second 00-59					|08			
%f	|Microsecond 000000-999999			|548513			
%z	|UTC offset					|+0100			
%Z	|Timezone					|CST			
%j	|Day number of year 001-366			|365			
%U	|Week num of year, Sunday as first day of week, 00-053		|52	
%W	|Week num of year, Monday as first day of week, 00-53		|52	
%c	|Local ver of date and time			|Mon Dec 31 17:41:00 2018
%C	|Century					|20			
%x	|Local version of date				|12/31/18		
%X	|Local version of time				|17:41:00		
%%	|A % character					|%			
%G	|ISO 8601 year					|2018			
%u	|ISO 8601 weekday (1-7)				|1			
%V	|ISO 8601 weeknumber (01-53)			|01			
"""


class App(tk.Tk):
    def __init__(self, support_file_types):
        tk.Tk.__init__(self)
        global SUPPORTED_FILE_TYPES
        SUPPORTED_FILE_TYPES = support_file_types
        self.mtdr = MetaDataReader(SUPPORTED_FILE_TYPES)
        self.config = configparser.ConfigParser()

        thisfolder = os.path.dirname(os.path.abspath(__file__))
        self.initfile = os.path.join(thisfolder, "config.ini")

        create_new = not os.path.exists(self.initfile)

        self.config.read(self.initfile)
        if create_new:
            self.config.add_section("main")
            print("added MAIN SECTION")
            self.config.set("main", "used_file_types", "")
            self.config.set("main", "textbox_input_dir", "")
            self.config.set("main", "textbox_output_dir", "")
            self.config.write(open(self.initfile, "w"))

        self.geometry("700x640")
        self.title("File Sorter")

        # input box
        self.button_change_input_dir = tk.Button(
            self,
            text="Browse Files",
            command=lambda: self.BrowseFiles(
                self.textbox_input_dir, "textbox_input_dir"
            ),
        )

        self.textbox_input_dir = tk.Entry(self, width=60, bg="light yellow")
        self.label_input_dir = tk.Label(self, text="Input Directory")
        # output box
        self.button_change_output_dir = tk.Button(
            self,
            text="Browse Files",
            command=lambda: self.BrowseFiles(
                self.textbox_output_dir, "textbox_output_dir"
            ),
        )
        self.textbox_output_dir = tk.Entry(self, width=60, bg="light yellow")
        self.label_output_dir = tk.Label(self, text="Output Directory")

        self.textbox_input_format = tk.Entry(self, width=60, bg="light yellow")
        self.label_input_format = tk.Label(self, text="Input format")

        # filetypes Check buttons -------------------------------------------------
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
        self.button_move = tk.Button(self, text="Move", command=self.move)

        # setting up the grid ------------------------------------------------------
        self.textbox_input_dir.grid(row=1, column=1)
        self.button_change_input_dir.grid(row=1, column=2)
        self.label_input_dir.grid(row=1, column=0)

        self.textbox_output_dir.grid(row=2, column=1)
        self.button_change_output_dir.grid(row=2, column=2)
        self.label_output_dir.grid(row=2, column=0)

        self.textbox_input_format.grid(row=3, column=1)
        self.label_input_format.grid(row=3, column=0)
        myTip = Hovertip(self.textbox_input_format, TOOLTIPTEXT)

        tk.Canvas(background="black", width=700, height=3).grid(
            row=6, column=0, columnspan=100
        )

        self.button_move.grid(row=7, column=1)

        # loading last saved settings ------------------------------------------------

        x = self.config["main"]["used_file_types"]
        x = [n.strip() for n in x[1:-1].replace("'", "").split(",")]
        print(x)
        self.used_file_types = x
        for x in self.Checkbutton_list:
            if x.cget("text") in self.used_file_types:
                x.select()

        y = self.config["main"]["textbox_input_dir"]
        print(y)
        self.textbox_input_dir.delete(0, "end")
        self.textbox_input_dir.insert(0, y)

        y = self.config["main"]["textbox_output_dir"]
        print(y)
        self.textbox_output_dir.delete(0, "end")
        self.textbox_output_dir.insert(0, y)

        # y = self.config["main"]["textbox_input_format"]
        # self.textbox_input_format.delete(0, "end")
        # self.textbox_input_format.insert(0, y)

        self.mainloop()

    ##----------------------------------------------------------------
    def write_to_config(self):
        with open(self.initfile, "w") as configfile:  # save
            self.config.write(configfile)

    def AddRemoveFileType(self, fileType):
        if fileType not in SUPPORTED_FILE_TYPES:
            return

        if fileType in self.used_file_types:
            self.used_file_types.remove(fileType)
        else:
            self.used_file_types.append(fileType)
        print(self.used_file_types)
        self.config["main"]["used_file_types"] = f"{self.used_file_types}"
        self.write_to_config()

    def BrowseFiles(self, textbox, name):
        filename = filedialog.askdirectory(
            # initialdir="/",
            initialdir="D:\\.backups\\phone backups\\pixel7ofek20230126\\DCIM\\Camera\\",
            title="Select a folder",
        )
        # Change label contents
        print(f"Selected {filename} as input directory")
        textbox.delete(0, "end")
        textbox.insert(0, filename)

        self.config["main"][name] = filename
        self.write_to_config()

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

                    ################################
                    match filename.split(".")[-1]:
                        case "jpg" | "png" | "wepg":
                            data = self.mtdr.imgDateExif(img_path)
                        case "mov" | "avi" | "mp4":
                            data = self.mtdr.DateExifTool(img_path)
                        case _:
                            data = None

                    # photo with no data
                    if data is None:
                        print("data IS NONE")
                        continue

                    ## this is NOT CHANGEABLE!!! THIS IS FORMAT OF RECEIVED DATA
                    ## AND NOT THE FORMAT OF THE FILENAMES!. dont change plz
                    tf = "%Y:%m:%d %H:%M:%S"
                    # 19 is the expected length of a date for the format string
                    pars_data = datetime.strptime(data[:19], tf)

                    folder_name = pars_data.strftime(self.textbox_input_format.get())

                    print(f"{filename} ||| {data}")
                    print(pars_data)
                    print(folder_name)

                    ################################

            ## progress bar updating
            files_compleated += 1
            pb["value"] = (files_compleated / lstdirlen) * 100
            pbroot.update()

        pbroot.destroy()


if __name__ == "__main__":
    pass
