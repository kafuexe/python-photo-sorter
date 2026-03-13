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

echo.
where iscc >nul 2>nul
if %ERRORLEVEL%==0 (
    echo Building installer...
    iscc installer.iss
    if exist "dist\PhotoSorterSetup.exe" (
        echo Installer built: dist\PhotoSorterSetup.exe
    ) else (
        echo Installer build FAILED.
        exit /b 1
    )
) else (
    echo Skipping installer ^(Inno Setup not found^)
)
