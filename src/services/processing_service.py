import logging
from typing import Callable

from ..models.file_result import FileResult
from ..models.processing_config import ProcessingConfig
from .steps.file_finder import FileFinder
from .steps.metadata_extractor import MetadataExtractor
from .steps.destination_resolver import DestinationResolver
from .steps.file_executor import FileExecutor

logger = logging.getLogger(__name__)


class ProcessingService:
    def __init__(self,
                 file_finder: FileFinder,
                 metadata_extractor: MetadataExtractor,
                 destination_resolver: DestinationResolver,
                 file_executor: FileExecutor):
        self._file_finder = file_finder
        self._metadata_extractor = metadata_extractor
        self._destination_resolver = destination_resolver
        self._file_executor = file_executor

    def process(self, config: ProcessingConfig,
                on_progress: Callable[[FileResult], None] | None = None) -> list[FileResult]:
        results: list[FileResult] = []

        files = self._file_finder.find(config.input_dir, config.selected_extensions)

        for file_path in files:
            result = FileResult(source=file_path)

            try:
                metadata = self._metadata_extractor.extract(file_path)
                result.metadata = metadata

                dest = self._destination_resolver.resolve(file_path, metadata, config)

                if dest is None:
                    result.status = "skipped"
                elif not metadata.get("date") and config.handle_unknown:
                    self._file_executor.execute(file_path, dest, config.action)
                    result.destination = dest
                    result.status = "unknown"
                else:
                    self._file_executor.execute(file_path, dest, config.action)
                    result.destination = dest
                    result.status = "success"

            except Exception as e:
                result.status = "error"
                result.error = str(e)
                logger.error("Error processing %s: %s", file_path, e)

            results.append(result)

            if on_progress:
                on_progress(result)

        return results
