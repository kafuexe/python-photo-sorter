import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from ..models.file_result import FileResult
from ..models.processing_config import ProcessingConfig
from ..steps.file_finder import BaseFileFinder
from ..steps.metadata_extractor import BaseMetadataExtractor
from ..steps.destination_resolver import BaseDestinationResolver
from ..steps.file_executor import BaseFileExecutor

logger = logging.getLogger(__name__)


@dataclass
class TimingStats:
    """Accumulated timing for each pipeline step."""
    find: float = 0.0
    extract: float = 0.0
    resolve: float = 0.0
    execute: float = 0.0
    total: float = 0.0
    file_count: int = 0
    _per_file: list[dict] = field(default_factory=list)

    def record(self, source: str, extract: float, resolve: float, execute: float) -> None:
        self._per_file.append({
            "file": source,
            "extract": extract,
            "resolve": resolve,
            "execute": execute,
        })

    @property
    def per_file(self) -> list[dict]:
        return self._per_file

    def summary(self) -> str:
        lines = [
            f"Total time:       {self.total:.3f}s",
            f"  File discovery:   {self.find:.3f}s",
            f"  Metadata extract: {self.extract:.3f}s  (avg {self._avg(self.extract)})",
            f"  Dest resolve:     {self.resolve:.3f}s  (avg {self._avg(self.resolve)})",
            f"  File execute:     {self.execute:.3f}s  (avg {self._avg(self.execute)})",
            f"  Files processed:  {self.file_count}",
        ]
        return "\n".join(lines)

    def slowest(self, n: int = 5) -> list[dict]:
        total_key = lambda f: f["extract"] + f["resolve"] + f["execute"]
        return sorted(self._per_file, key=total_key, reverse=True)[:n]

    def _avg(self, total: float) -> str:
        if self.file_count == 0:
            return "-"
        avg = total / self.file_count
        if avg < 0.001:
            return f"{avg * 1000:.2f}ms"
        return f"{avg:.3f}s"


class ProcessingService:
    def __init__(self,
                 file_finder: BaseFileFinder,
                 metadata_extractor: BaseMetadataExtractor,
                 destination_resolver: BaseDestinationResolver,
                 file_executor: BaseFileExecutor):
        self._file_finder = file_finder
        self._metadata_extractor = metadata_extractor
        self._destination_resolver = destination_resolver
        self._file_executor = file_executor

    def process(self, config: ProcessingConfig,
                on_progress: Callable[[FileResult], None] | None = None,
                on_total: Callable[[int], None] | None = None,
                cancel_event: threading.Event | None = None) -> tuple[list[FileResult], TimingStats]:
        stats = TimingStats()
        results: list[FileResult] = []

        t0 = time.perf_counter()

        t = time.perf_counter()
        files = self._file_finder.find(config.input_dir, config.selected_extensions)
        stats.find = time.perf_counter() - t

        if on_total:
            on_total(len(files))

        for file_path in files:
            # Check for cancellation before processing each file
            if cancel_event is not None and cancel_event.is_set():
                break

            result = FileResult(source=file_path)

            try:
                t = time.perf_counter()
                metadata = self._metadata_extractor.extract(file_path)
                t_extract = time.perf_counter() - t
                result.metadata = metadata

                t = time.perf_counter()
                dest = self._destination_resolver.resolve(file_path, metadata, config)
                t_resolve = time.perf_counter() - t

                t = time.perf_counter()
                if dest is None:
                    result.status = "skipped"
                elif config.dry_run:
                    result.destination = dest
                    result.status = "unknown" if (not metadata.get("date") and config.handle_unknown) else "success"
                elif not self._file_executor.execute(file_path, dest, config.action):
                    result.status = "skipped"
                elif not metadata.get("date") and config.handle_unknown:
                    result.destination = dest
                    result.status = "unknown"
                else:
                    result.destination = dest
                    result.status = "success"
                t_execute = time.perf_counter() - t

                stats.extract += t_extract
                stats.resolve += t_resolve
                stats.execute += t_execute
                stats.record(file_path.name, t_extract, t_resolve, t_execute)

            except Exception as e:
                result.status = "error"
                result.error = str(e)
                logger.error("Error processing %s: %s", file_path, e)

            results.append(result)

            if on_progress:
                on_progress(result)

        stats.total = time.perf_counter() - t0
        stats.file_count = len(results)
        logger.info("Timing:\n%s", stats.summary())

        return results, stats
