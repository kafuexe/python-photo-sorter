# Python Photo Sorter

A desktop app that organizes photos and videos into date-based folders using EXIF metadata.

## Features

- Sort photos and videos by date into customizable folder structures
- Multiple metadata backends (Pillow EXIF, ExifRead, PyExifTool)
- Supports many formats: JPEG, PNG, WebP, HEIC, TIFF, MP4, MOV, AVI, MKV, WMV, FLV
- Move or copy files
- Handles files without date data (moves to `.unknown` folder or skips)
- Customizable date format (e.g. `%Y/%m/%d` creates `2024/01/15/`)
- Auto-saves settings between sessions
- Operation logging — each move/copy creates a timestamped log with full file details
- Modern dark UI built with CustomTkinter
- Builds to a single shareable `.exe`

## Requirements

- Python 3.12+

## Installation

```bash
git clone <repo-url>
cd python-photo-sorter
pip install -r requirements.txt
```

## Usage

```bash
python -m src
```

## Building an Executable

```bash
pip install pyinstaller
build.bat
```

This produces `dist/PhotoSorter.exe` — a single file you can share. Config and logs are saved next to the exe.

## Testing

```bash
pytest tests/ -v
```

Tests also run automatically on push/PR via GitHub Actions.

## Project Structure

```
python-photo-sorter/
├── run.py                     # Entry point for PyInstaller
├── build.bat                  # Build script
├── photo_sorter.spec          # PyInstaller config
├── requirements.txt
├── src/
│   ├── __main__.py            # App entry point
│   ├── models/                # Data classes (FileResult, ProcessingConfig)
│   ├── handlers/              # Metadata extraction backends
│   ├── steps/                 # Pipeline steps (find, extract, resolve, execute)
│   ├── services/              # Config, processing, and log services
│   └── ui/                    # CustomTkinter UI
│       ├── app_window.py
│       ├── theme.py
│       ├── format_help_window.py
│       ├── assets/
│       └── widgets/
├── tests/
│   ├── models/
│   ├── handlers/
│   ├── services/
│   ├── steps/
│   └── test_e2e.py
└── .github/workflows/tests.yml
```

## Configuration

Settings are stored in `config.json` (created automatically on first run). Each move/copy operation writes a log file to the `move-log/` folder with the timestamp, settings, and status of every file processed.

### Date Format Codes

| Code | Description    | Example   |
|------|----------------|-----------|
| %Y   | Full year      | 2024      |
| %m   | Month          | 01        |
| %d   | Day            | 15        |
| %H   | Hour (24h)     | 14        |
| %M   | Minute         | 30        |
| %B   | Month name     | December  |
| %A   | Weekday name   | Wednesday |

Slashes in the format create subfolders. For example `%Y/%m/%d` creates `2024/01/15/`.

## License

MIT License
