@echo off
REM TIGHC Engine - Local PyInstaller build (Windows)
REM Usage: build.bat
REM
REM Builds a standalone GUI executable with PyInstaller, the same way CI
REM does for a tagged release (see .github/workflows/ci.yml's "build" job) -
REM installs requirements.txt + pyinstaller if missing, runs
REM scripts\build_exe.py (which drives PyInstaller via its argument API
REM rather than a hand-maintained .spec file), then renames the output to
REM match CI's naming convention (TIGHC-windows-vX.Y.Z.exe) so a local
REM build looks like a release download. Output lands in dist\, which is
REM gitignored - never committed.
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
%PY% scripts\build_exe.py
if errorlevel 1 exit /b 1

set /p VERSION=<VERSION.md
set "DEST=dist\TIGHC-windows-v%VERSION%.exe"
move /y "dist\TIGHC.exe" "%DEST%" >nul

echo Built %DEST%
