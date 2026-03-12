class PhotoSorterError(Exception):
    """Base exception for all photo sorter errors."""


class DirectoryNotFoundError(PhotoSorterError):
    """Input directory does not exist."""


class InvalidPathError(PhotoSorterError):
    """Path is not writable or contains invalid characters."""


class InvalidDateFormatError(PhotoSorterError):
    """Date format string is invalid."""


class HandlerError(PhotoSorterError):
    """A handler failed to process a file."""


class ConfigError(PhotoSorterError):
    """Config file is corrupt or unreadable."""
