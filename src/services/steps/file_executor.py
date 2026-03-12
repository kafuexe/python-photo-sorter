import shutil
from pathlib import Path


class FileExecutor:
    def execute(self, source: Path, dest: Path, action: str) -> None:
        """Move or copy file. Creates parent directories as needed.
        Handles filename collisions by appending incrementing suffix."""
        dest = self._resolve_collision(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if action == "move":
            shutil.move(str(source), str(dest))
        else:
            shutil.copy2(str(source), str(dest))

    @staticmethod
    def _resolve_collision(dest: Path) -> Path:
        if not dest.exists():
            return dest

        stem = dest.stem
        suffix = dest.suffix
        parent = dest.parent
        counter = 2

        while True:
            new_dest = parent / f"{stem} ({counter}){suffix}"
            if not new_dest.exists():
                return new_dest
            counter += 1
