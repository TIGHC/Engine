<p align="center">
  <img src="assets/logo.png" width="300" alt="The Intiface Game Haptics Controller (TIGHC)">
</p>

# The Intiface Game Haptics Controller (TIGHC)

> **18+ only.** This software connects to and controls adult haptic/sex toy
> devices based on your keyboard and mouse input while gaming. It is intended
> for use only by adults aged 18 or older. `gui.py` requires you to confirm
> this before it'll start.

**Version 6.0.0** — see [CHANGELOG.md](CHANGELOG.md) for release history.

Haptic feedback for your games, driven by the keys you're already pressing.

TIGHC links your keyboard/mouse input to a Buttplug/Intiface toy. Sneak,
sprint, attack, jump — each action can drive its own motor, at its own
intensity, per game. As much as I hate to say it this was made with grok,
chat gpt, and some claude. (I wish I was better at coding)

Website: https://tighc.stuxie.dev  
Repository: https://github.com/TIGHC/Engine  
License: [GPL-3.0-or-later](LICENSE.md)

## Quick start

Prefer not to install Python at all? Grab a standalone executable from the
**[latest release](https://github.com/TIGHC/Engine/releases/latest)** -
`TIGHC-windows.exe` / `TIGHC-linux` / `TIGHC-macos.zip`.
These are built automatically by CI from this same source (see
`.github/workflows/ci.yml` and `src/build/create_release_files.py`) - no separate
download needed. You can also browse every release, with download
links per platform, on the [Releases page](https://tighc.stuxie.dev/releases).

Running from source instead:

```
git clone https://github.com/TIGHC/Engine.git
python gui.py
```

This opens an interactive window: connect to Intiface, scan for devices,
assign nicknames to each motor/capability, build or edit game profiles, tune
global settings, and start/stop the haptics engine - all in one place.

If `python` doesn't work, try `py` instead, or call your Python install by
full path (Windows users on OneDrive-synced folders sometimes need this).

## Linux / Steam Deck

Windows is the primary target, but the engine also runs on Linux, including
Steam Deck's Desktop Mode - it needs an X11 session rather than Desktop
Mode's default Wayland one, since focused-window detection and global
input capture both require it. See **[the Linux &amp; Steam Deck guide](https://tighc.stuxie.dev/guides/linux)**
for the full setup walkthrough (switching sessions, installing dependencies,
getting Intiface Central running, troubleshooting). Everything else in this
README - profiles, the GUI - applies identically on Linux.

Standalone Linux, Windows, and macOS executables are built automatically for
every tagged release (see [Quick start](#quick-start) above) - actual Steam
Deck **Game Mode** support (as opposed to Desktop Mode, which already works
today) is still a roadmap item; see the Linux guide's note on this.

## Steam artwork

`assets/steam/` has a full set of custom Steam library artwork (grid
capsules, hero, logo, icon) for adding TIGHC to your Steam library as a
non-Steam game.

**[⬇ Download TIGHC_Steam_Assets.zip](https://github.com/TIGHC/Engine/raw/steam_assets/TIGHC_Steam_Assets.zip)**
— always up to date with the latest release, no need to clone the repo.
Also available as an asset on any [Release](https://github.com/TIGHC/Engine/releases).

## How it's organized

```
gui.py                       # entry point: QApplication setup, age gate, launches MainWindow
src/
  tighc.py                   # re-export facade over the modules below - not meant to be run directly
  engine.py                  # HapticsController - the engine itself
  haptics.py                 # configs/haptics.json load/apply + derived settings
  profiles.py                # profiles/<id>/profile.json loading
  devices.py                 # configs/devices.json registry + per-channel state
  input.py                   # keyboard/mouse normalization, focused-window lookup
  ranges.py                  # VibeRange/DurationRange/PulseSpec
  paths.py                   # filesystem layout (configs/, profiles/)
  metadata.py                # project name/repo URL
  version.py                 # version number + get_version()/get_version_tuple()
  updates.py                 # GitHub update check (About tab + startup)
  build/
    create_release_files.py  # PyInstaller build script (see "Development" below)
    create_project_assets.py # regenerates assets/icon.png/.ico/.icns/logo.png
                              # (and the sibling Website repo's copies)
    create_steam_assets.py   # regenerates assets/steam/ from icon.png/logo.png
  gui/                       # PySide6/Qt GUI
    theme.py                 # QSS light/dark tokens matching tighc.stuxie.dev's style.css
    age_gate.py               # the 18+ confirmation dialog
    workers.py                # AsyncBridge + Qt-thread marshaling helpers
    main_window.py            # window shell, top bar, tab widget
    devices_tab.py            # connection controls, channel list, rename
    profiles_tab.py           # profile picker/form, bindings table, binding editor dialog
    test_tab.py                # manual channel control + simulated-keybind triggers
    settings_tab.py            # haptics.json form + user-data-folder shortcuts
    run_tab.py                 # Start/Stop, live status, log viewer
    about_tab.py                # version/update-check, links, changelog viewer
assets/
  icon.png, icon.ico, icon.icns  # window/taskbar/macOS icon
  logo.png                    # About tab banner / age-gate logo
  author.png                  # avatar next to the author link on the About tab
  checkbox_check.png          # QCheckBox's checked-state icon (see src/gui/theme.py)
  steam/                      # Steam library artwork - see create_steam_assets.py above
tests/                        # pytest suite - see "Development" below
pyproject.toml                # project metadata/dependencies + pytest config
requirements.txt               # runtime dependencies (same list as pyproject.toml's)
CHANGELOG.md / VERSION.md      # release history + current version (semver)
CONTRIBUTING.md                # how to contribute a change
LICENSE.md                     # GPL-3.0-or-later
commit.sh / commit.bat         # commit + tag a release, reading the version from VERSION.md
.gitignore
.github/workflows/ci.yml       # tests on every push/PR; builds + publishes releases on a vX.Y.Z tag
%APPDATA%\TIGHC\  (~/Library/Application Support/TIGHC/ on macOS, ~/.local/share/TIGHC/ on Linux)  # per-user data, never touched by git
  profiles/                    # downloaded from TIGHC Profiles on GitHub on first launch
  configs/
    haptics.json               # global settings (connection, panic key, smoothing, ...)
    devices.json                # remembers a nickname for each connected motor/capability
  <your-other-game>/
    profile.json
```

`configs/` and its contents are created automatically (with sensible
defaults) the first time you run `gui.py` - you don't need to create them
yourself. Editing the JSON files by hand and using the GUI are fully
interchangeable - both just read/write the same files.

## Profiles: one per game

Your profiles live in `%APPDATA%\TIGHC\profiles\` (`~/Library/Application Support/TIGHC/profiles/`
on macOS, `~/.local/share/TIGHC/profiles/` on Linux). On first launch, TIGHC downloads all profiles from
[TIGHC Profiles](https://github.com/TIGHC/Profiles) on GitHub and
seeds them there. Profiles you edit are never overwritten automatically.

Each profile is a folder containing a single `profile.json` with the game's
window title(s), keybinds, and intensity ranges. The GUI watches whatever
window currently has focus and automatically switches to the matching profile -
so you can alt-tab between games and it just follows along.

The easiest way to add a new profile is the GUI's "New profile..." button.
Use "Update profiles from GitHub" in the Profiles tab to pick up any new
profiles added to the TIGHC Profiles repo. Want to share a profile you've
made? Open a pull request on [TIGHC Profiles](https://github.com/TIGHC/Profiles).

Each binding in `profile.json` has:

- **`keys`** - the key(s)/button(s) that trigger it (`w`, `space`, `ctrl`,
  `mouse_left`, `mouse_right`, `mouse_middle`, `scroll`, digits, etc.)
- **`mode`** - either:
  - `"continuous"` - a sustained vibration for as long as the key/button is
    held (e.g. movement, sneaking, holding down the mouse button).
  - `"pulse"` - a single randomized buzz each time it's pressed, regardless
    of how long it's held (e.g. jump, drop, opening inventory).
- **`devices`** - which channel(s) this binding drives: a list of nicknames
  from `configs/devices.json`, or `["all"]` (the default if omitted).
- **`enabled`** - set to `false` to turn a binding off without deleting it.

Each binding's `vibe` is a `[low, high]` intensity band (0.0–1.0). A random
value is rolled from the band each activation, so nothing feels perfectly
repetitive.

`priority` lists binding ids in "first match wins" order - useful when more
than one binding could apply at once (e.g. attacking should win over just
moving).

A `grounded_2` profile is included alongside `minecraft` as a second working
example (movement/sprint/crouch/attack/aim-block, jump/interact
/inventory/hotbar as pulses). It's built from Grounded's standard default
keybinds rather than anything sequel-specific - if Grounded 2 changes any of
them, just edit the profile in the GUI (or the JSON directly) to match.

## Test mode

The GUI's **Test** tab lets you check things work without needing the actual
game running:

- **Manual channel control** - a slider and "Pulse"/"Hold" controls per
  connected channel, driving it directly regardless of any profile. Good for
  confirming a toy responds and getting a feel for what an intensity % feels
  like.
- **Simulate keybinds** - pick a profile and "Pin" it as the active one
  (overriding the real focused-window detection), then trigger its pulse
  bindings or toggle its continuous bindings' "Hold" to simulate the
  corresponding key/button being pressed - exercising the exact same code
  path real input does. Continuous "Hold" only does something once you've
  hit Start on the Run tab, since that's what's actually computing output
  levels each tick.

"Stop all testing" releases every manual hold/pin at once if you want to bail
out quickly.

## Devices: one channel per motor/capability

Toys aren't addressed as a single on/off unit - every capability a device
exposes (each motor's vibrate, oscillate, rotate, etc.) is its own
independently controllable **channel**. A single-motor toy is one channel; a
dual-motor toy (e.g. Lovense Edge) is two, each targetable separately by a
different keybind; a device that supports both vibrating and oscillating
exposes both as separate channels too.

`configs/devices.json` remembers a friendly nickname for each channel so it
stays the same across reconnects and rescans. The GUI's Devices tab lists
everything found on scan and lets you rename any of them; a keybind then
targets one, several, or `"all"` of these nicknames via its `devices` field.

Position-based outputs (e.g. stroker-style "move to position X") aren't
supported - only continuous intensity-style outputs (vibrate, rotate,
oscillate, constrict, etc.) fit the "roll a random level" model this script
uses.

## Global settings

`configs/haptics.json` covers everything that isn't game- or
device-specific: the Intiface WebSocket URL, a master randomization
override, level smoothing, the panic key (forces everything off for a
moment), auto-reconnect, and the background tick rate. Edit it by hand or
via the GUI's Settings tab - either way, saving takes effect immediately,
no restart needed. The one exception is the WebSocket URL: an already-open
connection isn't automatically torn down and reopened just because the URL
changed, so click **"Connect + Scan"** (or Stop then Start) after changing
it to actually reconnect using the new one.

The Devices tab shows this URL (read-only there - Settings is the only
place that changes it) alongside **Connect + Scan**, **Rescan**, and
**Disconnect** buttons, and the top bar always shows the current connection
state ("Not connected" / "Connecting..." / "Connected - N channel(s)") no
matter which tab you're on.

## Development: tests and building executables

```
python -m venv .venv
.venv/Scripts/activate               # .venv/bin/activate on Linux/macOS
pip install -e ".[dev]"
pytest                              # runs tests/ - pure-logic coverage (profiles, ranges,
                                     # devices, haptics config, paths); no GUI/network/hardware
python src/build/create_release_files.py  # installs pyinstaller if missing, builds
                                           # dist/TIGHC.exe (dist/TIGHC on Linux,
                                           # dist/TIGHC.app on macOS) - no OS/version
                                           # in the name; CI's own "Collect build
                                           # artifacts" step adds that for release
                                           # downloads (TIGHC-windows.exe, etc.)
```

The test suite never touches your real `%APPDATA%\TIGHC` (or
`~/Library/Application Support/TIGHC`/`~/.local/share/TIGHC`) -
`tests/conftest.py` redirects it to a throwaway temp directory before
anything under `src/` is imported, so running `pytest` is always safe on a
machine that already has TIGHC configured. See
[CONTRIBUTING.md](CONTRIBUTING.md) for what's expected of a pull request.

## About, versioning, and contact

The GUI's **About** tab shows the current version, a short project summary,
the versioning scheme, the changelog, and a link to the repository. This
project follows [Semantic Versioning](https://semver.org/)
(`MAJOR.MINOR.PATCH`) - see [CHANGELOG.md](CHANGELOG.md) for what changed in
each release. Questions, issues, or contributions:
https://github.com/TIGHC/Engine

## License

Licensed under the [GPL-3.0-or-later](LICENSE.md).

---

*Written & Maintained by <img src="https://github.com/StuxieDev.png" height="14" alt="StuxieDev" valign="middle"> [StuxieDev](https://stuxie.dev).*

*[A StuxieDev Project](https://projects.stuxie.dev)*
