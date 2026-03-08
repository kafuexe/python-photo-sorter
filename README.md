# Python Photo Sorter

A Python-based photo and video organizer that sorts files by their EXIF date metadata.

## Features

- Organize photos and videos by date
- Supports multiple file formats (JPEG, PNG, WebP, MP4, MOV, AVI)
- Extracts date from image EXIF data or video Create Date
- Options to move or copy files
- Handle files without date data (move to .unknown folder or skip)

## Requirements

- Python 3.8+
- Pillow
- ExifTool

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Place `exiftool.exe` in the project root directory

## Usage

Run the application:

```bash
python main.py
```

## Project Structure

```
python-photo-sorter/
├── main.py                    # Entry point script
├── src/
│   ├── __init__.py           # Package init
│   ├── main.py               # Main application class
│   ├── config/
│   │   ├── __init__.py       # Config module
│   │   └── config_manager.py # Configuration handling
│   ├── core/
│   │   ├── __init__.py       # Core module
│   │   ├── meta_data_reader.py # Metadata reading functions
│   │   └── file_operations.py # File moving/copying functions
│   └── ui/
│       ├── __init__.py       # UI module
│       ├── constants.py      # UI constants and tooltips
│       ├── app_window.py     # Main application window
│       ├── directory_entry.py # Directory entry widget
│       └── checkbutton_group.py # File type checkbuttons
├── exiftool/                 # ExifTool executable
│   └── exiftool64.exe
├── config.ini                # Application configuration
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Configuration

Create/edit `config.ini` with the following settings:

```ini
[main]
used_file_types = ['jpg', 'png', 'wepg', 'mp4', 'avi', 'mov']
textbox_input_dir = D:\\path\\to\\input
 textbox_output_dir = D:\\path\\to\\output
 textbox_input_format = %%Y%%m%%d
 checkbutton_unknowdata_checkvar = 1
```

### Date Format

Use `%%Y%%m%%d` format. Examples:

- `%%Y%%m%%d` → `2024/01/15`
- `%%Y/%%m/%%d` → `2024/01/15`
- `%%Y-%%m-%%d` → `2024-01-15`

### Format Codes

| Code | Description | Example |
|------|-------------|---------|
| %%Y | Full year | 2024 |
| %%m | Month | 01 |
| %%d | Day | 15 |
| %%H | Hour | 14 |
| %%M | Minute | 30 |

## Compiling to Executable

1. Download [Auto-Py-To-Exe](https://www.auto-py-to-exe.com/)
2. Select the `main.py` file
3. Select the project folder as extra files (include `config.ini` and `exiftool`)
4. Choose your icon
5. Click Convert

## License

MIT License
