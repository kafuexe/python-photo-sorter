# Photo Sorter Refactor — Design Spec

## Overview

Complete refactor of the Python Photo Sorter application. The current codebase has tightly coupled UI and logic, hardcoded values, bugs, and an incomplete initial refactor. This redesign introduces a handler-based, pipeline-driven architecture that is extensible, testable, and maintainable.

## Goals

1. **Extensible** — adding new file types or metadata sources means writing one handler class
2. **Clean and maintainable** — proper separation of concerns, dependency injection, no hardcoded values
3. **Prepared for new features** — architecture supports undo, file count summaries, dry-run, new sorting strategies

## Tech Stack

- **UI:** tkinter (kept from current)
- **Config:** JSON (replacing INI/configparser)
- **Image metadata:** Pillow (kept)
- **Video/general metadata:** pyexiftool (Python wrapper — requires exiftool installed on system PATH)
- **Testing:** pytest (kept)

**Note on exiftool:** pyexiftool is a wrapper around the exiftool CLI, so exiftool must be installed on the system and available on PATH. On Windows, users must install exiftool separately (e.g., via `winget install exiftool` or manual download). The `PyExifToolHandler` checks for exiftool availability at registration time and logs a warning if not found — the app still works without it (Pillow + FileStatHandler cover most cases), but video metadata extraction will be unavailable.

---

## Project Structure

```
src/
  __init__.py
  __main__.py                       # Entry point & wiring
  models/
    __init__.py
    file_result.py                  # FileResult dataclass
    processing_config.py            # ProcessingConfig dataclass
  handlers/
    __init__.py
    base.py                         # Abstract BaseHandler
    registry.py                     # HandlerRegistry
    pillow_exif_handler.py          # EXIF via Pillow (jpg, png, webp)
    pyexiftool_handler.py           # Metadata via pyexiftool (all supported formats)
    file_stat_handler.py            # Fallback: file system dates
  services/
    __init__.py
    config_service.py               # JSON config load/save/defaults
    processing_service.py           # Pipeline coordinator
    steps/
      __init__.py
      file_finder.py                # Find files by extension
      metadata_extractor.py         # Run handlers, merge metadata
      destination_resolver.py       # Build output path from metadata + format
      file_executor.py              # Move or copy files
  ui/
    __init__.py
    app_window.py                   # Main window — pure presentation
    widgets/
      __init__.py
      directory_entry.py            # Label + entry + browse button
      checkbutton_group.py          # Dynamic checkbuttons from registry
  errors/
    __init__.py
    exceptions.py                   # Custom exception hierarchy
config.json                         # User config (replaces config.ini)
```

---

## Models

### FileResult

```python
@dataclass
class FileResult:
    source: Path                    # Original file path
    destination: Path | None        # Where it was moved/copied (None if skipped/error)
    status: str                     # "success", "skipped", "error", "unknown"
    error: str | None               # Error message if status == "error"
    metadata: dict                  # Accumulated metadata from handlers
```

Returned per-file by the processing service. The UI uses these for progress updates and the final summary.

### ProcessingConfig

```python
@dataclass
class ProcessingConfig:
    input_dir: Path                 # Source directory
    output_dir: Path                # Destination root directory
    date_format: str                # strftime format, e.g. "%Y/%m/%d"
    action: str                     # "move" or "copy"
    selected_extensions: list[str]  # e.g. ["jpg", "png", "mp4"]
    handle_unknown: bool            # Whether to move unknown-date files
    unknown_folder_name: str        # Default: ".unknown"
```

Built from UI state, passed to the processing service. Clean boundary between UI and logic.

**Note:** `action` is per-invocation (move vs. copy button click) and is not persisted in config. All other fields are saved/loaded.

`ProcessingConfig` provides `to_dict()` and `from_dict()` class methods for serialization to/from the JSON config. `ConfigService` uses these internally.

---

## Handlers

Handlers are organized by **extraction method**, not by file type. Multiple handlers can apply to the same file, each contributing different metadata.

### BaseHandler (Abstract)

```python
class BaseHandler(ABC):
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Extensions this handler can process, e.g. ['jpg', 'png']"""

    @abstractmethod
    def priority(self) -> int:
        """Execution order. Lower = runs first.
        Convention: 10 = native/fast, 50 = external tool, 100 = fallback"""

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> dict:
        """Extract metadata from file. Returns dict with extracted key-value pairs.
        Should include 'date' key (datetime | None) when date extraction is attempted.
        Returns empty dict if nothing could be extracted."""
```

### Concrete Handlers

**PillowExifHandler** (priority: 10)
- Extensions: jpg, png, webp
- Extracts: date (from EXIF DateTimeOriginal, DateTimeDigitized, DateTime), camera info
- Uses: Pillow

**PyExifToolHandler** (priority: 50)
- Extensions: jpg, png, webp, mov, avi, mp4 (and any format pyexiftool supports)
- Extracts: date (Create Date), additional metadata Pillow can't read
- Uses: pyexiftool

**FileStatHandler** (priority: 100)
- Extensions: `["*"]` (wildcard — universal fallback for any file type)
- Extracts: date from file system modified/created time
- Uses: os.stat / Path.stat()

### HandlerRegistry

```python
class HandlerRegistry:
    def register(self, handler: BaseHandler) -> None:
        """Register a handler for its declared extensions."""

    def get_handlers(self, extension: str) -> list[BaseHandler]:
        """Returns all handlers for this extension, sorted by priority (lowest first).
        Always includes handlers registered with wildcard ["*"] extension."""

    def get_all_extensions(self) -> set[str]:
        """Returns union of all extensions from all registered handlers.
        Excludes the wildcard "*" — only returns concrete extensions."""
```

### Processing Flow for a .jpg

1. `PillowExifHandler` (priority 10) — extracts EXIF date, camera info
2. `PyExifToolHandler` (priority 50) — fills in anything Pillow missed
3. `FileStatHandler` (priority 100) — fallback if no date found above

First handler to return a valid `date` wins. Other metadata keys accumulate across handlers.

### Adding a New Handler

1. Create a class extending `BaseHandler`
2. Implement `supported_extensions()`, `priority()`, `extract_metadata()`
3. Register it in `__main__.py` — nothing else changes, UI auto-discovers new extensions

---

## Services

### ConfigService

```python
class ConfigService:
    def __init__(self, config_path: Path = None):
        """Defaults to config.json in project root."""

    def load(self) -> dict:
        """Load config from JSON. Returns defaults if file missing."""

    def save(self, config: dict) -> None:
        """Save config dict to JSON."""

    def get_defaults(self) -> dict:
        """Returns default configuration values."""
```

**Config JSON structure:**

```json
{
    "input_dir": "",
    "output_dir": "",
    "date_format": "%Y/%m/%d",
    "selected_extensions": ["jpg", "png", "webp", "mov", "avi", "mp4"],
    "handle_unknown": true,
    "unknown_folder_name": ".unknown"
}
```

### Processing Pipeline

The `ProcessingService` coordinates four injectable steps. Each step is defined as a Protocol (structural typing) so that any object with the right method signature can be used — no inheritance required. The default implementations are concrete classes that satisfy these protocols.

#### ProcessingService (Coordinator)

```python
class ProcessingService:
    def __init__(self,
                 file_finder: FileFinder,
                 metadata_extractor: MetadataExtractor,
                 destination_resolver: DestinationResolver,
                 file_executor: FileExecutor):
        """Each step is injectable."""

    def process(self, config: ProcessingConfig,
                on_progress: Callable[[FileResult], None] = None) -> list[FileResult]:
        """Runs the pipeline: find -> extract -> resolve dest -> execute.
        Calls on_progress per file for live UI updates.
        Returns list of FileResults for summary."""
```

#### Pipeline Steps

**FileFinder** — Locates files to process.

```python
class FileFinder:
    def find(self, directory: Path, extensions: list[str]) -> list[Path]:
        """Recursively find files matching given extensions."""
```

Swap example: a `ZipFileFinder` that reads from archives.

**MetadataExtractor** — Runs handlers and merges results.

```python
class MetadataExtractor:
    def __init__(self, registry: HandlerRegistry):

    def extract(self, file_path: Path) -> dict:
        """Run all applicable handlers in priority order.
        First valid 'date' wins. Other keys accumulate."""
```

**DestinationResolver** — Builds the output path.

```python
class DestinationResolver:
    def resolve(self, file_path: Path, metadata: dict,
                config: ProcessingConfig) -> Path | None:
        """Build destination path from metadata date + format string.
        Returns None if no date found and handle_unknown is False.
        Returns path in unknown_folder if no date and handle_unknown is True."""
```

Swap example: a `GpsDestinationResolver` that sorts by location.

**FileExecutor** — Performs the file operation.

```python
class FileExecutor:
    def execute(self, source: Path, dest: Path, action: str) -> None:
        """Move or copy file. Creates parent directories as needed."""
```

Swap example: a `DryRunExecutor` that logs without touching files, or a `LoggingExecutor` that records operations for undo.

#### Filename Collision Handling

When `DestinationResolver` produces a path that already exists, `FileExecutor` appends an incrementing suffix: `photo.jpg` → `photo (2).jpg` → `photo (3).jpg`, etc. This happens in `FileExecutor` (not the resolver) so that custom resolvers don't need to worry about it. If the collision check itself fails, the file is recorded as a `FileResult` with status `"error"`.

---

## UI Layer

### AppWindow

```python
class AppWindow(tk.Tk):
    def __init__(self,
                 config_service: ConfigService,
                 processing_service: ProcessingService,
                 registry: HandlerRegistry):
        """Receives all dependencies. Creates no services."""

    def _build_ui(self) -> None:
        """Compose widgets and lay out the window."""

    def _on_move(self) -> None:
        """Build config with action='move', call processing service."""

    def _on_copy(self) -> None:
        """Build config with action='copy', call processing service."""

    def _on_progress(self, result: FileResult) -> None:
        """Callback: update UI with per-file progress."""

    def _on_complete(self, results: list[FileResult]) -> None:
        """Show summary: files processed, skipped, errors, unknowns."""

    def _on_closing(self) -> None:
        """Save current UI state to config via ConfigService."""

    def _build_config(self, action: str) -> ProcessingConfig:
        """Read current UI state into a ProcessingConfig dataclass."""
```

- Zero business logic — just reads UI state, calls services, displays results
- Config loaded on start, saved on close
- Processing results displayed via callbacks

#### Threading

Processing runs in a background thread (`threading.Thread`) to avoid freezing the UI. The `on_progress` callback posts updates to the main thread via `root.after()`. The move/copy buttons are disabled during processing and re-enabled on completion. `_on_complete` is also posted via `root.after()` to safely update the UI from the background thread.

### Widgets

**DirectoryEntry** — Reusable composite widget.

```python
class DirectoryEntry(tk.Frame):
    """Label + text entry + browse button.
    Methods: get() -> str, set(path: str) -> None"""
```

**CheckbuttonGroup** — Dynamically built from registry.

```python
class CheckbuttonGroup(tk.Frame):
    def __init__(self, parent, extensions: set[str]):
        """Creates one checkbutton per extension.
        Extensions come from registry.get_all_extensions() — no hardcoded list."""

    def get_selected(self) -> list[str]
    def set_selected(self, extensions: list[str]) -> None
```

---

## App Bootstrap

All wiring in one place — the only file that knows about concrete classes:

```python
# __main__.py
def main():
    # 1. Services
    config_service = ConfigService()

    # 2. Handlers
    registry = HandlerRegistry()
    registry.register(PillowExifHandler())
    registry.register(PyExifToolHandler())
    registry.register(FileStatHandler())

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
    app.mainloop()

if __name__ == "__main__":
    main()
```

---

## Error Handling

```python
# errors/exceptions.py
class PhotoSorterError(Exception):
    """Base exception for all photo sorter errors."""

class DirectoryNotFoundError(PhotoSorterError):
    """Input directory does not exist."""

class InvalidPathError(PhotoSorterError):
    """Path is not writable or contains invalid characters."""

class InvalidDateFormatError(PhotoSorterError):
    """Date format string is invalid."""

class HandlerError(PhotoSorterError):
    """A handler failed to process a file."""

class ConfigError(PhotoSorterError):
    """Config file is corrupt or unreadable."""
```

Handlers should catch their own internal errors and return empty dict rather than crashing. `HandlerError` is for unrecoverable handler failures. The processing service catches all errors per-file and records them in `FileResult.error`.

---

## Migration from Current Code

### What Gets Deleted

- `src/main.py` (PhotoSorterApp class — logic moves to services)
- `src/ui/app_window.py` (rebuilt from scratch, no inherited logic)
- `src/ui/constants.py` (tooltip text moves into new app_window, invalid chars into destination_resolver)
- `src/core/meta_data_reader.py` (replaced by handlers)
- `src/core/file_operations.py` (replaced by file_executor + file_finder)
- `src/config/config_manager.py` (replaced by config_service)
- `src/utils/path_utils.py` (validation moves into file_finder/destination_resolver)
- `config.ini` (replaced by config.json)

**Note:** The current `photo_sort_errors.py` defines `class FileNotFoundError` which shadows Python's built-in. This is intentionally dropped in the new exception hierarchy — use the built-in `FileNotFoundError` instead.

### What Gets Kept (Conceptually)

- EXIF tag reading logic (moves into PillowExifHandler)
- File move/copy logic (moves into FileExecutor)
- UI layout concepts (rebuilt cleaner in new AppWindow)
- Tooltip text content (moves into new UI)

### Dependencies Change

**Remove:** iniconfig, colorama, Pygments (unused in app)
**Add:** pyexiftool
**Keep:** Pillow, pytest

---

## Future Features Enabled by This Architecture

- **File count summary** — `ProcessingService.process()` returns `list[FileResult]`, trivial to count by status
- **Undo** — swap `FileExecutor` with `LoggingExecutor` that records operations to a log file, then replay in reverse
- **Dry run** — swap `FileExecutor` with `DryRunExecutor`
- **New file types** — write a handler, register it
- **New sorting strategies** — swap `DestinationResolver` (by GPS, by camera, by file size, etc.)
- **CLI mode** — wire services to argparse instead of tkinter, same processing pipeline
- **Progress bar** — `on_progress` callback already built in
