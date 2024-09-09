from PIL import Image
import os
from Main import SUPPORTED_FILE_TYPES


def get_date_taken(path):
    exif = Image.open(path).getexif()
    if not exif:
        raise Exception("Image {0} does not have EXIF data.".format(path))
    return exif[36867]


from datetime import datetime
from PIL import Image

# import time

from datetime import datetime
from PIL import Image

# import time


def imgDate(fn):
    "returns the image date from image (if available)\nfrom Orthallelous"
    std_fmt = "%Y:%m:%d  %H:%M:%S.%f"
    # for subsecond prec, see doi.org/10.3189/2013JoG12J126 , sect. 2.2, 2.3
    tags = [
        (36867, 37521),  # (DateTimeOriginal, SubsecTimeOriginal)
        (36868, 37522),  # (DateTimeDigitized, SubsecTimeDigitized)
        (306, 37520),
    ]  # (DateTime, SubsecTime)
    exif = Image.open(fn)._getexif()

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
    T = datetime.strptime(full, std_fmt)
    # T = time.mktime(time.strptime(dat, '%Y:%m:%d %H:%M:%S')) + float('0.%s' % sub)
    return T


path = r"D:\.backups\google photos\22022024\Google Photos\Photos from 2024"  # test

i = 0
folder = os.path.join(path, "")
for filename in os.listdir(folder):
    try:
        for ftype in SUPPORTED_FILE_TYPES:
            if filename.endswith(ftype):

                img_path = os.path.join(folder, filename)
                data = imgDate(img_path)
                print(f"{filename} {data}")
                break
    except Exception as e:
        print(e)
