# need to read exif and xmp for matadeta
# c:\RecentlyUploadedPhotos\YYYYMMDD

from UserInterface import App

SUPPORTED_FILE_TYPES = ["jpg", "png", "wepg", "mov", "avi", "mp4"]
if __name__ == "__main__":
    App(support_file_types=SUPPORTED_FILE_TYPES)
