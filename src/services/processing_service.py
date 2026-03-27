import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable

from ..models.file_result import FileResult
from ..models.processing_config import ProcessingConfig
from ..steps.file_finder import BaseFileFinder
from ..steps.metadata_extractor import BaseMetadataExtractor
from ..steps.destination_resolver import BaseDestinationResolver
from ..steps.file_executor import BaseFileExecutor

logger = logging.getLogger(__name__)


# =====================
# Timing
# =====================

@dataclass
class TimingStats:
    find: float = 0.0
    extract: float = 0.0
    resolve: float = 0.0
    execute: float = 0.0
    total: float = 0.0
    file_count: int = 0
    _per_file: list[dict] = field(default_factory=list)

    def record(self, file: str, extract: float, resolve: float, execute: float) -> None:
        self._per_file.append({
            "file": file,
            "extract": extract,
            "resolve": resolve,
            "execute": execute,
        })

    @property
    def per_file(self) -> list[dict]:
        return self._per_file

    def slowest(self, n: int = 5) -> list[dict]:
        return sorted(
            self._per_file,
            key=lambda f: f["extract"] + f["resolve"] + f["execute"],
            reverse=True
        )[:n]

    def summary(self) -> str:
        return "\n".join([
            f"Total time:       {self.total:.3f}s",
            f"  File discovery:   {self.find:.3f}s",
            f"  Metadata extract: {self.extract:.3f}s  (avg {self._avg(self.extract)})",
            f"  Dest resolve:     {self.resolve:.3f}s  (avg {self._avg(self.resolve)})",
            f"  File execute:     {self.execute:.3f}s  (avg {self._avg(self.execute)})",
            f"  Files processed:  {self.file_count}",
        ])

    def _avg(self, total: float) -> str:
        if self.file_count == 0:
            return "-"
        avg = total / self.file_count
        return f"{avg * 1000:.2f}ms" if avg < 0.001 else f"{avg:.3f}s"


# =====================
# Service
# =====================

class ProcessingService:
    def __init__(
        self,
        file_finder: BaseFileFinder,
        metadata_extractor: BaseMetadataExtractor,
        destination_resolver: BaseDestinationResolver,
        file_executor: BaseFileExecutor,
    ):
        self._finder = file_finder
        self._extractor = metadata_extractor
        self._resolver = destination_resolver
        self._executor = file_executor

    # ---------------------
    # Public API
    # ---------------------

    def process(
        self,
        config: ProcessingConfig,
        on_progress: Callable[[FileResult], None] | None = None,
        on_total: Callable[[int], None] | None = None,
        cancel_event: threading.Event | None = None,
    ) -> tuple[list[FileResult], TimingStats]:

        stats = TimingStats()
        results: list[FileResult] = []
        claimed_dests: set[str] = set()

        start_total = time.perf_counter()

        file_paths, stats.find = self._timed(
            lambda: self._finder.find(config.input_dir, config.selected_extensions)
        )

        if on_total:
            on_total(len(file_paths))

        for file_path in file_paths:
            if cancel_event and cancel_event.is_set():
                break

            result = self._process_file(file_path, config, stats, claimed_dests)
            results.append(result)

            if on_progress:
                on_progress(result)

        stats.total = time.perf_counter() - start_total
        stats.file_count = len(results)

        logger.info("Timing:\n%s", stats.summary())
        return results, stats

    # ---------------------
    # Internal
    # ---------------------

    def _process_file(
        self,
        file_path,
        config: ProcessingConfig,
        stats: TimingStats,
        claimed_dests: set[str],
    ) -> FileResult:

        result = FileResult(source=file_path)

        try:
            metadata, t_extract = self._timed(
                lambda: self._extractor.extract(file_path)
            )

            destination, t_resolve = self._timed(
                lambda: self._resolver.resolve(file_path, metadata, config)
            )

            (status, final_dest), t_execute = self._timed(
                lambda: self._execute(file_path, destination, metadata, config, claimed_dests)
            )

            result.metadata = metadata
            result.destination = final_dest
            result.status = status

            stats.extract += t_extract
            stats.resolve += t_resolve
            stats.execute += t_execute
            stats.record(file_path.name, t_extract, t_resolve, t_execute)

        except Exception as e:
            result.status = "error"
            result.error = str(e)
            logger.exception("Error processing %s", file_path)

        return result

    def _execute(self, file_path, destination, metadata, config, claimed_dests):
        if destination is None:
            return "skipped", None

        if config.dry_run:
            key = str(destination)
            if destination.exists() or key in claimed_dests:
                return "skipped", None

            claimed_dests.add(key)
            status = "unknown" if (not metadata.get("date") and config.handle_unknown) else "success"
            return status, destination

        if not self._executor.execute(file_path, destination, config.action):
            return "skipped", None

        if not metadata.get("date") and config.handle_unknown:
            return "unknown", destination

        return "success", destination

    @staticmethod
    def _timed(fn: Callable[[], any]) -> tuple[any, float]:
        start = time.perf_counter()
        result = fn()
        return result, time.perf_counter() - start