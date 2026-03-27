import logging
import threading
from typing import Callable

from ..models.file_result import FileResult, FileStatus
from ..models.processing_config import ProcessingConfig
from ..steps.file_finder import BaseFileFinder
from ..steps.metadata_extractor import BaseMetadataExtractor
from ..steps.destination_resolver import BaseDestinationResolver
from ..steps.file_executor import BaseFileExecutor
from ..utils.timing import timed, TimingStats

logger = logging.getLogger(__name__)

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

        def run_pipeline():
            file_paths, stats.find = timed(
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

        _, stats.total = timed(run_pipeline)
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
            metadata, t_extract = timed(
                lambda: self._extractor.extract(file_path)
            )

            destination, t_resolve = timed(
                lambda: self._resolver.resolve(file_path, metadata, config)
            )

            (status, final_dest), t_execute = timed(
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
            result.status = FileStatus.error
            result.error = str(e)
            logger.exception("Error processing %s", file_path)

        return result

    def _execute(self, file_path, destination, metadata, config, claimed_dests):
        if destination is None:
            return FileStatus.skipped, None

        if config.dry_run:
            key = str(destination)
            if destination.exists() or key in claimed_dests:
                return FileStatus.skipped, None

            claimed_dests.add(key)
            status = FileStatus.unknown if (not metadata.get("date") and config.handle_unknown) else FileStatus.success
            return status, destination

        if not self._executor.execute(file_path, destination, config.action):
            return FileStatus.skipped, None

        if not metadata.get("date") and config.handle_unknown:
            return FileStatus.unknown, destination

        return FileStatus.success, destination