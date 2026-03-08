"""Custom exceptions for the photo sorter application."""


class PhotoSorterError(Exception):
    """Base exception for all photo sorter errors."""
    pass


class FileNotFoundError(PhotoSorterError):
    """Raised when a required file is not found."""
    pass


class DirectoryNotFoundError(PhotoSorterError):
    """Raised when a required directory is not found."""
    pass


class InvalidDateFormatError(PhotoSorterError):
    """Raised when the provided date format is invalid."""
    pass


class InvalidPathError(PhotoSorterError):
    """Raised when a path is invalid or not accessible."""
    pass
