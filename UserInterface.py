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
import sys
from pathlib import Path
import shutil
import errno, os

FORMAT_TOOLTIPTEXT = """
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

UNKNOWN_TOOLTIP = """If Checked - Any image or video without an associated date
will be moved to a dedicated folder name \".unknown\" 

If Unchecked - The aforementioned images or videos will not 
be moved\\copied and will be LEFT AS IS (without regard to if the user
has Chosen to move or to Copy the images in the folder)"""

ERROR_INVALID_NAME = 123


class App(tk.Tk):
    def __init__(self, support_file_types):
        tk.Tk.__init__(self)
        os.system("")
        global SUPPORTED_FILE_TYPES
        SUPPORTED_FILE_TYPES = support_file_types
        self.mtdr = MetaDataReader(SUPPORTED_FILE_TYPES)
        self.config = configparser.ConfigParser()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

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
            self.config.set("main", "textbox_input_format", "")

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
            x.grid(column=10, row=pos, sticky="w")

        for i in range(len(self.Checkbutton_list)):
            pass

        # other ----------------------------------------------------------------
        self.checkbutton_unknowdata_checkvar = tk.IntVar()
        self.checkbutton_unknowdata = tk.Checkbutton(
            text="Move Unknown Data?",
            variable=self.checkbutton_unknowdata_checkvar,
            command=self.unknowdata_checkmark_update,
            onvalue=1,
            offvalue=0,
        )

        self.button_move = tk.Button(
            self,
            text="Move",
            command=lambda move=self.move_file: self.main_move_copy(move),
        )
        self.button_copy = tk.Button(
            self,
            text="Copy",
            command=lambda copy=self.copy_file: self.main_move_copy(copy),
        )
        # setting up the grid ------------------------------------------------------
        self.textbox_input_dir.grid(row=1, column=1, columnspan=5)
        self.button_change_input_dir.grid(row=1, column=8)
        self.label_input_dir.grid(row=1, column=0)

        self.textbox_output_dir.grid(row=2, column=1, columnspan=5)
        self.button_change_output_dir.grid(row=2, column=8)
        self.label_output_dir.grid(row=2, column=0)

        self.textbox_input_format.grid(row=3, column=1, columnspan=5)
        self.label_input_format.grid(row=3, column=0)
        format_tooltip = Hovertip(self.textbox_input_format, FORMAT_TOOLTIPTEXT)
        unknown_tooltip = Hovertip(self.checkbutton_unknowdata, UNKNOWN_TOOLTIP)
        tk.Canvas(background="black", width=700, height=3).grid(
            row=6, column=0, columnspan=100
        )

        self.button_move.grid(row=7, column=1)
        self.button_copy.grid(row=7, column=2)
        self.checkbutton_unknowdata.grid(row=7, column=3)

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

        y = self.config["main"]["textbox_input_format"].replace("%%", "%")
        self.textbox_input_format.delete(0, "end")
        self.textbox_input_format.insert(0, y)

        y = self.config["main"]["checkbutton_unknowdata_checkvar"]
        print(y)
        val = tk.IntVar()
        val.set(int(y))
        self.checkbutton_unknowdata_checkvar = val
        if self.checkbutton_unknowdata_checkvar.get() == 1:
            print("i selected!")
            self.checkbutton_unknowdata.select()

        self.mainloop()

    ##----------------------------------------------------------------

    def move_file(self, filename, filepath, outputpath):
        Path(outputpath).mkdir(parents=True, exist_ok=True)
        shutil.move(filepath, os.path.join(outputpath, filename))

    def copy_file(self, filename, filepath, outputpath):
        Path(outputpath).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(filepath, os.path.join(outputpath, filename))

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

    def unknowdata_checkmark_update(self):
        val = self.checkbutton_unknowdata_checkvar.get()

        y = tk.IntVar()
        y.set(int(abs(val - 1)))

        self.checkbutton_unknowdata_checkvar = y
        val = self.checkbutton_unknowdata_checkvar.get()
        self.config["main"]["checkbutton_unknowdata_checkvar"] = f"{val}"
        print(f"UPDATING CHECKMARK: {val}")
        self.write_to_config()

    def BrowseFiles(self, textbox, name):
        filename = filedialog.askdirectory(
            # initialdir="/",
            initialdir="D:\\.backups\\phone backups\\pixel7ofek20230126\\DCIM\\Camera\\",
            title="Select a folder",
        )
        # Change label contents
        print(f"Selected {filename} as input directory")
        if not filename:
            return
        textbox.delete(0, "end")
        textbox.insert(0, filename)

        self.config["main"][name] = filename
        self.write_to_config()

    def is_pathname_valid(self, pathname: str) -> bool:
        """
        `True` if the passed pathname is a valid pathname for the current OS;
        `False` otherwise.
        """
        # If this pathname is either not a string or is but is empty, this pathname
        # is invalid.
        try:
            if not isinstance(pathname, str) or not pathname:
                return False

            # Strip this pathname's Windows-specific drive specifier (e.g., `C:\`)
            # if any. Since Windows prohibits path components from containing `:`
            # characters, failing to strip this `:`-suffixed prefix would
            # erroneously invalidate all valid absolute Windows pathnames.
            _, pathname = os.path.splitdrive(pathname)

            # Directory guaranteed to exist. If the current OS is Windows, this is
            # the drive to which Windows was installed (e.g., the "%HOMEDRIVE%"
            # environment variable); else, the typical root directory.
            root_dirname = (
                os.environ.get("HOMEDRIVE", "C:")
                if sys.platform == "win32"
                else os.path.sep
            )
            assert os.path.isdir(root_dirname)  # ...Murphy and her ironclad Law

            # Append a path separator to this directory if needed.
            root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

            # Test whether each path component split from this pathname is valid or
            # not, ignoring non-existent and non-readable path components.
            for pathname_part in pathname.split(os.path.sep):
                try:
                    os.lstat(root_dirname + pathname_part)
                # If an OS-specific exception is raised, its error code
                # indicates whether this pathname is valid or not. Unless this
                # is the case, this exception implies an ignorable kernel or
                # filesystem complaint (e.g., path not found or inaccessible).
                #
                # Only the following exceptions indicate invalid pathnames:
                #
                # * Instances of the Windows-specific "WindowsError" class
                #   defining the "winerror" attribute whose value is
                #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
                #   fine-grained and hence useful than the generic "errno"
                #   attribute. When a too-long pathname is passed, for example,
                #   "errno" is "ENOENT" (i.e., no such file or directory) rather
                #   than "ENAMETOOLONG" (i.e., file name too long).
                # * Instances of the cross-platform "OSError" class defining the
                #   generic "errno" attribute whose value is either:
                #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
                #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
                except OSError as exc:
                    if hasattr(exc, "winerror"):
                        if exc.winerror == ERROR_INVALID_NAME:
                            return False
                    elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                        return False
        # If a "TypeError" exception was raised, it almost certainly has the
        # error message "embedded NUL character" indicating an invalid pathname.
        except TypeError as exc:
            return False
        # If no exception was raised, all path components and hence this
        # pathname itself are valid. (Praise be to the curmudgeonly python.)
        else:
            return True
        # If any other exception was raised, this is an unrelated fatal issue
        # (e.g., a bug). Permit this exception to unwind the call stack.
        #
        # Did we mention this should be shipped with Python already?

    def is_path_creatable(self, pathname: str) -> bool:
        """
        `True` if the current user has sufficient permissions to create the passed
        pathname; `False` otherwise.
        """
        # Parent directory of the passed path. If empty, we substitute the current
        # working directory (CWD) instead.
        dirname = os.path.dirname(pathname) or os.getcwd()
        return os.access(dirname, os.W_OK)

    def is_path_exists_or_creatable(self, pathname: str) -> bool:
        """
        `True` if the passed pathname is a valid pathname for the current OS _and_
        either currently exists or is hypothetically creatable; `False` otherwise.

        This function is guaranteed to _never_ raise exceptions.
        """
        try:
            # To prevent "os" module calls from raising undesirable exceptions on
            # invalid pathnames, is_pathname_valid() is explicitly called first.
            return self.is_pathname_valid(pathname) and (
                os.path.exists(pathname) or self.is_path_creatable(pathname)
            )
        # Report failure on non-fatal filesystem complaints (e.g., connection
        # timeouts, permissions issues) implying this path to be inaccessible. All
        # other exceptions are unrelated fatal issues and should not be caught here.
        except OSError:
            return False

    def throw_error_message(self, message="", detail=""):
        tk.messagebox.showerror(title="Error", message=message, detail=detail)

    def my_progressbar(self):
        root = tk.Tk()
        root.geometry("400x50")
        pb = Progressbar(
            root, length=100, mode="determinate", maximum=100, takefocus=True
        )
        pb["value"] = 0
        pb.grid(row=1, column=1)
        return root, pb

    def main_move_copy(self, movecopy_func):
        response = tk.messagebox.askyesno(
            title="Are you Sure?",
            message="""one last time before moving files, make sure all
            settings are correct, if you are sure click yes""",
            default="no",
        )
        if not response:
            return

        if self.checkbutton_unknowdata_checkvar.get() == 1:
            print("IM ON FFS")
        else:
            print("IM OFF FFS")

        folder = self.textbox_input_dir.get()
        user_outputdir = self.textbox_output_dir.get()
        user_format = self.textbox_input_format.get()

        if not os.path.exists(folder):
            self.throw_error_message("Input path is invalid")
            return
        if not os.path.exists(user_outputdir):
            self.throw_error_message("output path is invalid")
            return
        if any(
            cher in user_format
            for cher in ["/", ">", "<", ":", '"', "\\", "|", "?", "*"]
        ):
            self.throw_error_message(
                message="""Input format is invalid""",
                detail="It may contain Invalid characters such as: \n / , > , < , : , '' , \\ , | , ? , *",
            )
            return

        lstdirlen = len(os.listdir(folder))
        files_compleated = 0
        self.pbroot, pb = self.my_progressbar()
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
                        if self.checkbutton_unknowdata_checkvar.get() == 1:
                            movecopy_func(
                                filename,
                                img_path,
                                os.path.join(user_outputdir, ".unknown"),
                            )
                        continue

                    ## this is NOT CHANGEABLE!!! THIS IS FORMAT OF RECEIVED DATA
                    ## AND NOT THE FORMAT OF THE FILENAMES!. dont change plz
                    tf = "%Y:%m:%d %H:%M:%S"
                    # 19 is the expected length of a date for the format string
                    pars_data = datetime.strptime(data[:19], tf)
                    folder_name = pars_data.strftime(user_format)
                    folder_path = os.path.join(user_outputdir, folder_name)

                    if not self.is_path_exists_or_creatable(folder_path):
                        self.throw_error_message(
                            message="path dosent exists AND Not creatable",
                            detail=f"""path:{folder_path} \n , the program will regard any 
                            files that are to be moved\\copied to this path as without data.""",
                        )
                        if self.checkbutton_unknowdata_checkvar.get() == 1:
                            movecopy_func(
                                filename,
                                img_path,
                                os.path.join(user_outputdir, ".unknown"),
                            )

                        continue

                    print(f"{filename} ||| {data}")
                    print(pars_data)
                    print(folder_name)
                    movecopy_func(filename, img_path, folder_path)
                    print(f"{movecopy_func.__name__}")
                    ################################

            ## progress bar updating
            files_compleated += 1
            pb["value"] = (files_compleated / lstdirlen) * 100
            self.pbroot.update()

        self.pbroot.destroy()

    def on_closing(self):

        self.config["main"]["used_file_types"] = f"{self.used_file_types}"
        self.config["main"]["textbox_input_dir"] = f"{self.textbox_input_dir.get()}"
        self.config["main"]["textbox_output_dir"] = f"{self.textbox_output_dir.get()}"
        val = self.checkbutton_unknowdata_checkvar.get()
        self.config["main"]["checkbutton_unknowdata_checkvar"] = f"{val}"

        self.config["main"][
            "textbox_input_format"
        ] = self.textbox_input_format.get().replace("%", "%%")

        self.destroy()
        try:
            self.pbroot.destroy()
        except:
            pass

        self.write_to_config()
        print("exiting")
        sys.exit()


if __name__ == "__main__":
    pass
