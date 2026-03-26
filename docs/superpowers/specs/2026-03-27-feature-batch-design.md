# Feature Batch Design Spec

**Date:** 2026-03-27
**Scope:** 5 new features for Photo Sorter
**Status:** Draft

---

## Overview

Five features that extend the photo sorter's extraction coverage, add a non-destructive preview mode, and improve the processing UI. Each feature is independent and can be implemented/shipped separately.

**Build order:** Filename handlers → PyMediaInfoHandler → Enhanced progress → Dry run with tree preview

---

## Feature 1: Filename Pattern Handlers

### Goal

Extract dates from common device/app naming conventions when EXIF metadata is absent. One handler per naming convention, following the same architecture as `WhatsAppHandler`.

### Handlers

| Handler | Example Filename | Regex (on stem) | Extensions | Priority |
|---------|-----------------|-----------------|------------|----------|
| `SamsungHandler` | `20240615_143022.jpg` | `^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$` | jpg, jpeg, mp4 | 10 |
| `PixelHandler` | `PXL_20240615_143022.jpg` | `^PXL_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})` | jpg, jpeg, mp4 | 10 |
| `TelegramHandler` | `photo_2024-06-15_14-30-00.jpg` | `^(?:photo\|video)_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})` | jpg, jpeg, mp4 | 10 |
| `ScreenshotHandler` | `Screenshot_20240615-143022.png` | `^Screenshot_(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})` | png, jpg, jpeg | 10 |
| `DatestampHandler` | `2024-06-15 14.30.00.jpg` | `^(\d{4})-(\d{2})-(\d{2})[_ ](\d{2})\.(\d{2})\.(\d{2})` | jpg, jpeg, png, mp4 | 15 |

### Design Details

- Each handler lives in its own file under `src/handlers/` (e.g., `samsung_handler.py`)
- Each follows the `BaseHandler` interface: `supported_extensions()`, `priority()`, `extract_metadata(file_path)`
- Pattern matching uses a compiled `re.compile(..., re.IGNORECASE)` regex on `file_path.stem`
- All handlers extract both date and time (hours, minutes, seconds) into the returned `datetime`, unlike WhatsApp which only extracts date
- Invalid dates (e.g., month 13, Feb 30 on non-leap year) caught by `datetime()` constructor raising `ValueError` → return `{}`
- `SamsungHandler` uses a strict end-of-string anchor (`$`) to avoid false positives on arbitrary numeric filenames
- `DatestampHandler` at priority 15 runs after device-specific handlers — it's a generic "looks like a date" fallback
- All handlers registered in `__main__.py`

### Testing

- One test file per handler under `tests/handlers/`
- Same structure as `test_whatsapp_handler.py`: fixture, parameterized valid cases, parameterized rejection cases, edge cases (leap year, case insensitivity)

### Files

- `src/handlers/samsung_handler.py` (new)
- `src/handlers/pixel_handler.py` (new)
- `src/handlers/telegram_handler.py` (new)
- `src/handlers/screenshot_handler.py` (new)
- `src/handlers/datestamp_handler.py` (new)
- `src/__main__.py` (modified — register all new handlers)
- `tests/handlers/test_samsung_handler.py` (new)
- `tests/handlers/test_pixel_handler.py` (new)
- `tests/handlers/test_telegram_handler.py` (new)
- `tests/handlers/test_screenshot_handler.py` (new)
- `tests/handlers/test_datestamp_handler.py` (new)

---

## Feature 2: PyMediaInfoHandler

### Goal

Extract dates from video files (MP4, MOV, AVI, MKV, etc.) using the `pymediainfo` library, which bundles the native MediaInfo library in its pip wheels — no external system installs required.

### Handler Details

- **File:** `src/handlers/pymediainfo_handler.py`
- **Class:** `PyMediaInfoHandler`
- **Extensions:** `mp4, mov, avi, mkv, wmv, flv, 3gp, webm`
- **Priority:** 50 (external tool tier — slower than filename/EXIF, runs after them)
- **Dependency:** `pymediainfo` added to `requirements.txt`

### Date Extraction Logic

1. Call `MediaInfo.parse(str(file_path))` to get track metadata
2. Iterate the "General" track and check date fields in priority order:
   - `Tagged_Date`
   - `Encoded_Date`
   - `File_Modified_Date`
3. Parse the date string — MediaInfo returns dates like `UTC 2024-06-15 14:30:00` or `2024-06-15 14:30:00`
4. Strip `UTC ` prefix if present, parse with `%Y-%m-%d %H:%M:%S`
5. Return `{"date": datetime}` or `{}` if nothing found

### Availability Check

- At `__init__`, attempt to import `pymediainfo` and call `MediaInfo.can_parse()`
- If the library isn't installed or native lib fails: set `self._available = False`, log a warning
- `extract_metadata()` returns `{}` immediately when unavailable
- The app works without pymediainfo — it just won't extract video metadata from container headers

### Testing

- Mock `MediaInfo.parse()` return values
- Test tag priority order (Tagged_Date wins over Encoded_Date)
- Test UTC prefix stripping
- Test unavailability fallback (returns `{}`)
- Test missing/empty General track
- Test exception handling during parse

### Files

- `src/handlers/pymediainfo_handler.py` (new)
- `src/__main__.py` (modified — register handler)
- `requirements.txt` (modified — add pymediainfo)
- `tests/handlers/test_pymediainfo_handler.py` (new)

---

## Feature 3: Enhanced Progress Stats

### Goal

Show detailed live statistics during processing: elapsed time, ETA, throughput, per-status counters, and the current file with its outcome.

### Current State

The progress frame shows:
- A progress bar
- A `processed/total` label
- The status bar shows the current filename

### New Layout

```
[████████████████████░░░░░░░░░░] 87/142
12.3s elapsed — ~2.1s remaining — 7.1 files/sec
✓ 72 sorted  ⬡ 8 unknown  ⊘ 5 skipped  ✗ 2 errors
Processing: IMG_20240615.jpg → 2024/06/15/IMG_20240615.jpg
```

Four rows in the progress frame:
1. **Progress bar + count** — existing, unchanged
2. **Timing line** — elapsed time, ETA, throughput (files/sec)
3. **Status breakdown** — live counters for success/unknown/skipped/error
4. **Current file line** — source filename + destination path or status

### Implementation

All changes in `ProcessingController`:

- Add `_start_time: float` — set to `time.perf_counter()` when processing starts
- Add `_success_count`, `_unknown_count`, `_skipped_count`, `_error_count` — reset to 0 at start, incremented in `_on_progress()` based on `result.status`
- Add 3 new `ctk.CTkLabel` widgets to the progress frame (timing, breakdown, current file)
- ETA calculation: `(elapsed / processed) * remaining_count`
- Throughput: `processed / elapsed`
- All labels updated in `_on_progress()` via the existing `window.after(0, ...)` pattern (thread-safe)
- Status bar (`_status_var`) continues to show the final summary after completion

### No Pipeline Changes

All data comes from the existing `on_progress` callback and `FileResult` objects. No changes to `ProcessingService` or any handler.

### Files

- `src/ui/processing_controller.py` (modified)

---

## Feature 4: Dry Run with Tree Preview

### Goal

A non-destructive "Dry Run" mode that simulates processing and shows a live folder tree of what the output directory would look like, with a stop button and summary stats.

### Pipeline Changes

**ProcessingConfig:**
- Add field `dry_run: bool = False`
- `to_dict()` and `from_dict()` do NOT persist this field — it's a runtime-only option

**ProcessingService.process():**
- When `config.dry_run` is True, skip the `self._file_executor.execute()` call
- Still run finder, extractor, and resolver to produce real source → destination mappings
- Status assignment: files that would succeed get status `"success"`, unknown files get `"unknown"` — same as normal mode. The UI context (dry run) communicates that nothing was actually moved/copied.

### UI Changes

**Dry Run button:**
- Added to the action frame, left of Copy and Move:
  ```
  [Dry Run]  [Copy Files]  [Move Files]
  ```
- Styled like the Copy button (secondary/outlined) — non-destructive, feels safe
- No confirmation dialog needed
- During a dry run, button text changes to "Stop"
- Clicking "Stop" sets a `threading.Event` checked by the processing loop after each file

**Stop mechanism:**
- Add `_cancel_event: threading.Event` to `ProcessingController`
- Pass it to `ProcessingService.process()` as an optional `cancel_event` parameter
- In the processing loop, check `cancel_event.is_set()` after each file — if set, break out of the loop and return results so far
- Reset the event at the start of each run

**Tree preview panel:**
- A new frame that appears below the progress area when dry run starts
- Uses `tkinter.ttk.Treeview` (built into tkinter, no new dependency)
- Shows the output folder structure that would be created:
  ```
  📁 output/
  ├── 📁 2024/
  │   ├── 📁 06/
  │   │   └── 📁 15/
  │   │       ├── photo1.jpg
  │   │       └── photo2.jpg
  │   └── 📁 12/
  │       └── 📁 25/
  │           └── winter.jpg
  └── 📁 .unknown/
      └── nodate.jpg
  ```
- Tree nodes inserted live via `on_progress` callback:
  - Each result's `destination` path (relative to output_dir) is split into parts
  - Parent folder nodes created as needed (deduplication via a dict mapping path → tree node ID)
  - File leaf nodes appended under their folder
  - Tree auto-scrolls to show newest additions
- Panel hidden with `grid_remove()` when not in use

**Stats summary:**
- Shown below the tree after completion or stop:
  ```
  Would sort 142 files, 3 unknown, 0 errors
  ```
- Reuses the status breakdown counters from Feature 3

**Window resizing:**
- `minsize` height increases when tree panel is visible (475 → 700)
- Tree frame gets remaining vertical space via `grid_rowconfigure(weight=1)`
- Restored to original minsize when tree is dismissed

### Files

- `src/models/processing_config.py` (modified — add `dry_run` field)
- `src/services/processing_service.py` (modified — skip executor when dry_run, support cancel_event)
- `src/ui/processing_controller.py` (modified — dry run button, stop button, tree panel)
- `src/ui/app_window.py` (modified — add dry run button to layout, wire up tree panel)
- `tests/services/test_processing_service.py` (modified — test dry_run mode, cancel_event)
- `tests/models/test_processing_config.py` (modified — test dry_run field)

---

## Cross-Cutting Concerns

### Handler Registration Order

All handlers registered in `__main__.py` in this order:

```python
registry.register(PillowExifHandler())      # priority 10, EXIF
registry.register(ExifReadHandler())         # priority 20, EXIF
registry.register(WhatsAppHandler())         # priority 10, filename
registry.register(SamsungHandler())          # priority 10, filename
registry.register(PixelHandler())            # priority 10, filename
registry.register(TelegramHandler())         # priority 10, filename
registry.register(ScreenshotHandler())       # priority 10, filename
registry.register(DatestampHandler())        # priority 15, filename
registry.register(PyMediaInfoHandler())      # priority 50, video metadata
```

The first handler to return a date wins. For files with both EXIF data and a device-named filename, EXIF wins because PillowExifHandler is registered first (same priority = registration order breaks ties within the registry's sorted list).

### Error Handling

All handlers follow the existing pattern: catch exceptions internally, log at debug level, return `{}`. A failing handler never blocks the pipeline.

### Dependencies

- `pymediainfo` added to `requirements.txt` (bundled native lib via pip wheels, no system install needed)
- No other new dependencies — `ttk.Treeview` is part of the Python standard library

### Testing Strategy

- Each new handler: dedicated test file, fixtures, parameterized valid/invalid cases
- PyMediaInfoHandler: mocked MediaInfo.parse(), test tag priority and availability
- ProcessingService: test dry_run skips executor, test cancel_event stops loop
- ProcessingConfig: test dry_run field defaults and exclusion from to_dict/from_dict
- UI changes: not unit tested (CustomTkinter widgets aren't easily testable), verified manually
