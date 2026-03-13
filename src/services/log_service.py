import logging
import sys
from datetime import datetime
from pathlib import Path

from ..models.file_result import FileResult
from ..models.processing_config import ProcessingConfig

logger = logging.getLogger(__name__)

LOG_DIR_NAME = "move-log"


def _base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[2]


class LogService:
    def __init__(self, log_dir: Path | None = None):
        self._log_dir = log_dir or (_base_dir() / LOG_DIR_NAME)

    def write(self, config: ProcessingConfig, results: list[FileResult]) -> Path:
        self._log_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        filename = now.strftime("%Y-%m-%d_%H-%M-%S") + f"_{config.action}.txt"
        path = self._log_dir / filename

        lines: list[str] = []

        # Header
        lines.append(f"Photo Sorter — {config.action.upper()} log")
        lines.append(f"Date: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Settings
        lines.append("=== Settings ===")
        lines.append(f"  Source:      {config.input_dir}")
        lines.append(f"  Output:      {config.output_dir}")
        lines.append(f"  Date format: {config.date_format}")
        lines.append(f"  Action:      {config.action}")
        lines.append(f"  Extensions:  {', '.join(sorted(config.selected_extensions))}")
        lines.append(f"  Handle unknown: {config.handle_unknown}")
        lines.append("")

        # Summary
        success = sum(1 for r in results if r.status == "success")
        unknown = sum(1 for r in results if r.status == "unknown")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")
        lines.append("=== Summary ===")
        lines.append(f"  Total: {len(results)}  |  Success: {success}  |  Unknown: {unknown}  |  Skipped: {skipped}  |  Errors: {errors}")
        lines.append("")

        # File list
        lines.append("=== Files ===")
        for r in results:
            status = r.status.upper()
            dest = str(r.destination) if r.destination else "-"
            line = f"  [{status:>7}]  {r.source}  ->  {dest}"
            if r.error:
                line += f"  ({r.error})"
            lines.append(line)

        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Log written to %s", path)
        return path
