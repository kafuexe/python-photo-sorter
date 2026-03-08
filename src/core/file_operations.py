"""File operations for moving and copying files."""
import os
from pathlib import Path
import shutil


def move_file(source_path: str, dest_path: str) -> bool:
    """Move a file from source to destination.

    Args:
        source_path: Path to the source file.
        dest_path: Path to the destination directory.

    Returns:
        True if successful, False otherwise.
    """
    try:
        Path(dest_path).mkdir(parents=True, exist_ok=True)
        shutil.move(source_path, dest_path)
        return True
    except (OSError, shutil.Error):
        return False


def copy_file(source_path: str, dest_path: str) -> bool:
    """Copy a file from source to destination.

    Args:
        source_path: Path to the source file.
        dest_path: Path to the destination directory.

    Returns:
        True if successful, False otherwise.
    """
    try:
        Path(dest_path).mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest_path)
        return True
    except (OSError, shutil.Error):
        return False


def validate_source_path(path: str) -> bool:
    """Validate that a source path exists and is a directory.

    Args:
        path: Path to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(path, str) or not path.strip():
        return False

    path_obj = Path(path)
    return path_obj.exists() and path_obj.is_dir()


def validate_dest_path(path: str) -> bool:
    """Validate that a destination path is accessible for writing.

    Args:
        path: Path to validate.

    Returns:
        True if valid and writable, False otherwise.
    """
    if not isinstance(path, str) or not path.strip():
        return False

    try:
        path_obj = Path(path)
        # Check if path exists
        if path_obj.exists():
            return path_obj.is_dir() and os.access(path_obj, os.W_OK)
        else:
            # Check if parent directory exists and is writable
            parent = path_obj.parent
            return parent.exists() and os.access(parent, os.W_OK)
    except (OSError, PermissionError):
        return False


def get_matching_files(directory: str, extensions: list[str]) -> list[str]:
    """Get list of files with matching extensions in directory.

    Args:
        directory: Directory to search.
        extensions: List of file extensions (without dot).

    Returns:
        List of matching file paths.
    """
    if not Path(directory).exists():
        return []

    matching = []
    for file_path in Path(directory).iterdir():
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in extensions:
                matching.append(str(file_path))

    return matching
