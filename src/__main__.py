import logging
import signal
import sys

from .services.config_service import ConfigService
from .handlers.registry import HandlerRegistry
from .handlers.pillow_exif_handler import PillowExifHandler
from .handlers.exifread_handler import ExifReadHandler
from .handlers.pyexiftool_handler import PyExifToolHandler
from .steps import FileFinder, MetadataExtractor, DestinationResolver, FileExecutor
from .services.processing_service import ProcessingService
from .ui.app_window import AppWindow

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger.info("Starting Photo Sorter")

    # 1. Services
    config_service = ConfigService()

    # 2. Handlers
    registry = HandlerRegistry()
    registry.register(PillowExifHandler())
    registry.register(ExifReadHandler())
    registry.register(PyExifToolHandler())

    # 3. Pipeline steps
    file_finder = FileFinder()
    metadata_extractor = MetadataExtractor(registry)
    destination_resolver = DestinationResolver()
    file_executor = FileExecutor()

    # 4. Processing service
    processing_service = ProcessingService(
        file_finder=file_finder,
        metadata_extractor=metadata_extractor,
        destination_resolver=destination_resolver,
        file_executor=file_executor,
    )

    # 5. UI
    app = AppWindow(config_service, processing_service, registry)

    def safe_exit(*_):
        logger.info("Interrupted — saving config before exit")
        try:
            app._save_config()
        except Exception:
            pass
        app.destroy()
        sys.exit(0)

    signal.signal(signal.SIGINT, safe_exit)

    try:
        app.mainloop()
    except Exception:
        logger.exception("Unexpected crash — saving config before exit")
        try:
            app._save_config()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
