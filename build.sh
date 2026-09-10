#!/bin/bash
# TIGHC Engine - Local PyInstaller build
# Usage: ./build.sh
#
# Builds a standalone GUI executable with PyInstaller, the same way CI does
# for a tagged release (see .github/workflows/ci.yml's "build" job) -
# installs requirements.txt + pyinstaller if missing, runs `pyinstaller
# --noconfirm tighc-gui.spec`, then renames the output to match CI's naming
# convention (TIGHC-<os>-vX.Y.Z) so a local build looks like a release
# download. Output lands in dist/, which is gitignored - never committed.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PYTHON="$(command -v python3 || command -v python)"
if [ -z "$PYTHON" ]; then
    echo "Python 3 is required to build TIGHC" >&2
    exit 1
fi

"$PYTHON" -m pip install -q -r requirements.txt
"$PYTHON" -m pip install -q pyinstaller

# Linux needs Tk installed separately (it's not a pip package) to bundle
# tkinter - same note as ci.yml's "Install Tk (Linux only)" step.
if [ "$(uname -s)" = "Linux" ] && ! "$PYTHON" -c "import tkinter" >/dev/null 2>&1; then
    echo "tkinter isn't available to $PYTHON - install it first (e.g. sudo apt install python3-tk tk-dev)" >&2
    exit 1
fi

"$PYTHON" -m PyInstaller --noconfirm tighc-gui.spec

VERSION="$(tr -d '[:space:]' < VERSION.md)"
case "$(uname -s)" in
    Linux*)  os_name="linux";   ext="" ;;
    Darwin*) os_name="macos";   ext="" ;;
    *)       os_name="windows"; ext=".exe" ;;
esac
DEST="dist/TIGHC-${os_name}-v${VERSION}${ext}"
mv "dist/TIGHC${ext}" "$DEST"

echo "Built $DEST"
