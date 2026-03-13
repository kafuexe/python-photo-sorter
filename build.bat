@echo off
echo Building Photo Sorter...
pyinstaller photo_sorter.spec --clean -y
echo.
if exist "dist\PhotoSorter.exe" (
    echo Build complete: dist\PhotoSorter.exe
) else (
    echo Build FAILED — check output above for errors.
    exit /b 1
)
