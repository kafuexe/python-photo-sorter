from pathlib import Path


class FileFinder:
    def find(self, directory: Path, extensions: list[str]) -> list[Path]:
        """Recursively find files matching given extensions."""
        if not directory.is_dir():
            return []

        ext_set = {f".{e.lower().lstrip('.')}" for e in extensions}
        results = []

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ext_set:
                results.append(file_path)

        return sorted(results)
