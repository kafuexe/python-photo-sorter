# need to read exif and xmp for matadeta
# c:\RecentlyUploadedPhotos\YYYYMMDD
SUPPORTED_FILE_TYPES = {"jpg", "png", "wepg", "mov", "avi", "mp4"}
from MetaDataRead import SUPPORTED_FILE_TYPES
from UserInterface import App

if __name__ == "__main__":
    App(support_file_types=SUPPORTED_FILE_TYPES)
