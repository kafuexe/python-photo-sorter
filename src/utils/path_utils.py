import os


def is_path_creatable(self, path: str) -> bool:
    """Check if directory is writable."""
    try:
        parent = os.path.dirname(path) or os.getcwd()
        return os.access(parent, os.W_OK)
    except OSError:
        return False