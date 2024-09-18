from PIL import Image
import os
from datetime import datetime
import subprocess
import time


class MetaDataReader:
    def __init__(self, SUPPORTED_FILE_TYPES):
        self.supported_file_types = SUPPORTED_FILE_TYPES

    def imgDateExif(self, path):
        TIME_FORMAT = "%Y/%m/%d %H:%M:%S.%f"
        "returns the image date from image (if available)\nfrom Orthallelous"

        # for subsecond prec, see doi.org/10.3189/2013JoG12J126 , sect. 2.2, 2.3
        tags = [
            (36867, 37521),  # (DateTimeOriginal, SubsecTimeOriginal)
            (36868, 37522),  # (DateTimeDigitized, SubsecTimeDigitized)
            (306, 37520),
        ]  # (DateTime, SubsecTime)
        exif = Image.open(path).getexif()

        for t in tags:
            dat = exif.get(t[0])
            sub = exif.get(t[1], 0)

            # PIL.PILLOW_VERSION >= 3.0 returns a tuple
            dat = dat[0] if type(dat) == tuple else dat
            sub = sub[0] if type(sub) == tuple else sub
            if dat != None:
                break

        if dat == None:
            return None
        full = "{}.{}".format(dat, sub)

        # T = time.mktime(time.strptime(dat, "%Y:%m:%d %H:%M:%S")) + float("0.%s" % sub)
        return full

    def DateExifTool(self, path):
        TIME_FORMAT = "%d/%m/%Y %H:%M:%S.%f"
        EXIFTOOL_DATE_TAG_VIDEOS = "Create Date"

        exif_tool_path = os.path.join(
            os.path.abspath(os.getcwd()), "exiftool\\exiftool64.exe"
        )

        process = subprocess.Popen(
            [exif_tool_path, path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        out, err = process.communicate()

        lines = out.decode("utf-8").split("\n")
        for l in lines:
            if EXIFTOOL_DATE_TAG_VIDEOS in str(l):
                datetime_str = str(l.split(" :")[1].strip())

                # dt = datetime.strptime(datetime_str, TIME_FORMAT)
                return datetime_str

    ## ----------------------------------------------------------------
    ##testing functions

    def maintest(self, path):
        # test
        folder = os.path.join(path, "")
        # print(os.listdir(folder))
        for filename in os.listdir(folder):

            data = None
            if filename.endswith(tuple(self.supported_file_types)):
                img_path = os.path.join(folder, filename)
                if os.path.isfile(img_path):

                    match filename.split(".")[-1]:
                        case "jpg" | "png" | "wepg":
                            data = self.imgDateExif(img_path)
                        case "mov" | "avi" | "mp4":
                            data = self.DateExifTool(img_path)

                        case _:
                            data = None
            print(f"{filename} ||| {data}")

    def timetest(self, path, usege):
        """conclusion of time testing: DateExifTool is VERY slow,
        but it the only thing that works on video files
        if possible, use imgDateExif instead."""
        start = time.time()
        folder = os.path.join(path, "")
        for filename in os.listdir(folder):
            data = None
            if filename.endswith("jpg"):
                img_path = os.path.join(folder, filename)
                if os.path.isfile(img_path):
                    match usege:
                        case 1:
                            data = self.imgDateExif(img_path)
                        case 2:
                            data = self.DateExifTool(img_path)

        end = time.time()
        return f"case{usege} Time: {end - start}"

        # print("imgDateExif --------")
        # print(timetest(path, 1))
        # print(timetest(path, 1))
        # print(timetest(path, 1))
        # print(timetest(path, 1))
        # print("imgDateExif --------")
        # print("DateExifTool --------")
        # print(timetest(path, 2))
        # print(timetest(path, 2))
        # print(timetest(path, 2))
        # print(timetest(path, 2))
        # print("DateExifTool --------")


if __name__ == "__main__":
    # D:\.backups\phone backups\pixel7ofek20230126\DCIM\Camera\
    path = r"D:\\.backups\\phone backups\\pixel7ofek20230126\DCIM\\Camera\\"
    test_SUPPORTED_FILE_TYPES = ["jpg", "png", "wepg", "mov", "avi", "mp4"]
    x = MetaDataReader(test_SUPPORTED_FILE_TYPES)
    x.maintest(path)
