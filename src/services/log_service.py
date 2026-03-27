import logging
import sys
from datetime import datetime
from pathlib import Path

from ..models.file_result import FileResult, FileStatus
from ..models.processing_config import ProcessingConfig

logger = logging.getLogger(__name__)

LOG_DIR_NAME = "move-log"


def _base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[2]


def _format_result(r: FileResult) -> str:
    status = str(r.status.value).upper()
    dest = str(r.destination) if r.destination else "-"
    line = f"  [{status:>7}]  {r.source}  ->  {dest}"
    if r.error:
        line += f"  ({r.error})"
    return line


class LogService:
    def __init__(self, log_dir: Path | None = None):
        self._log_dir = log_dir or (_base_dir() / LOG_DIR_NAME)
        self._file = None
        self._path: Path | None = None

    def begin(self, config: ProcessingConfig) -> Path:
        """Open the log file and write the header. Call log_result() for each
        file, then finish() when done."""
        self._log_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        filename = now.strftime("%Y-%m-%d_%H-%M-%S") + f"_{config.action}.txt"
        self._path = self._log_dir / filename

        self._file = open(self._path, "w", encoding="utf-8")

        self._writeln(f"Photo Sorter — {config.action.upper()} log")
        self._writeln(f"Date: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self._writeln("")
        self._writeln("=== Settings ===")
        self._writeln(f"  Source:      {config.input_dir}")
        self._writeln(f"  Output:      {config.output_dir}")
        self._writeln(f"  Date format: {config.date_format}")
        self._writeln(f"  Action:      {config.action}")
        self._writeln(f"  Extensions:  {', '.join(sorted(config.selected_extensions))}")
        self._writeln(f"  Handle unknown: {config.handle_unknown}")
        self._writeln("")
        self._writeln("=== Files ===")
        self._file.flush()

        return self._path

    def log_result(self, result: FileResult) -> None:
        """Append a single file result and flush immediately."""
        if self._file is None:
            return
        self._writeln(_format_result(result))
        self._file.flush()

    def finish(self, results: list[FileResult], stats=None) -> None:
        """Write summary and timing, then close the log file."""
        if self._file is None:
            return

        self._writeln("")

        success = sum(1 for r in results if r.status == FileStatus.success)
        unknown = sum(1 for r in results if r.status == FileStatus.unknown)
        skipped = sum(1 for r in results if r.status == FileStatus.skipped)
        errors = sum(1 for r in results if r.status == FileStatus.error)
        self._writeln("=== Summary ===")
        self._writeln(f"  Total: {len(results)}  |  Success: {success}  |  Unknown: {unknown}  |  Skipped: {skipped}  |  Errors: {errors}")
        self._writeln("")

        if stats is not None:
            self._writeln("=== Timing ===")
            self._writeln(stats.summary())
            self._writeln("")

            slowest = stats.slowest(10)
            if slowest:
                self._writeln("=== Slowest Files ===")
                for f in slowest:
                    total = f["extract"] + f["resolve"] + f["execute"]
                    self._writeln(
                        f"  {total:.3f}s  {f['file']}"
                        f"  (extract={f['extract']:.3f}s  resolve={f['resolve']:.3f}s  execute={f['execute']:.3f}s)"
                    )

        self._file.close()
        self._file = None
        logger.info("Log written to %s", self._path)

    def _writeln(self, line: str) -> None:
        self._file.write(line + "\n")
