@echo off
REM TIGHC Engine - Local PyInstaller build (Windows)
REM Usage: build.bat
REM
REM Builds a standalone GUI executable with PyInstaller, the same way CI
REM does for a tagged release (see .github/workflows/ci.yml's "build" job) -
REM installs requirements.txt + pyinstaller if missing, runs `pyinstaller
REM --noconfirm tighc-gui.spec`, then renames the output to match CI's
REM naming convention (TIGHC-windows-vX.Y.Z.exe) so a local build looks like
REM a release download. Output lands in dist\, which is gitignored - never
REM committed.
setlocal
set "DIR=%~dp0"
cd /d "%DIR%"

where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo Python 3 is required to build TIGHC
        exit /b 1
    )
    set "PY=py"
) else (
    set "PY=python"
)

%PY% -m pip install -q -r requirements.txt
%PY% -m pip install -q pyinstaller
%PY% -m PyInstaller --noconfirm tighc-gui.spec
if errorlevel 1 exit /b 1

set /p VERSION=<VERSION.md
set "DEST=dist\TIGHC-windows-v%VERSION%.exe"
move /y "dist\TIGHC.exe" "%DEST%" >nul

echo Built %DEST%
