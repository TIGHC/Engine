<p align="center">
  <img src="assets/logo.png" width="300" alt="The Intiface Game Haptics Controller (TIGHC)">
</p>

# Contributing to TIGHC

Issues and pull requests are welcome at
[github.com/TIGHC/Engine](https://github.com/TIGHC/Engine).

## Getting set up

```
git clone https://github.com/TIGHC/Engine.git
cd Engine
python -m venv .venv
.venv/Scripts/activate   # .venv/bin/activate on Linux/macOS
pip install -e ".[dev]"
python gui.py
```

See the [README](README.md) for how the engine is organized (`src/`) and
what each module does.

## Making a change

Run the automated test suite before opening a PR (already installed via the
`.[dev]` extra above):

```
pytest
```

`tests/` covers the pure-logic modules (profile parsing/validation, intensity
ranges, device nickname resolution, `haptics.json` load/merge/apply, paths,
version) - it doesn't touch your real per-user TIGHC data directory (see
`tests/conftest.py`), and doesn't cover the GUI, the engine's asyncio/input
loop, or anything needing a real Intiface connection or toy. For those, verify
manually:

- The GUI's **Test** tab lets you simulate keybinds and drive channels
  directly without needing the real game or a connected toy.
- If you touched profile loading/parsing, also confirm a profile still loads
  cleanly from `%APPDATA%\TIGHC\profiles\` (`~/Library/Application Support/TIGHC/profiles/`
  on macOS, `~/.local/share/TIGHC/profiles/` on Linux) - a structurally invalid profile should fail fast with a clear
  error, not crash mid-session.
- If you touched Linux-specific code (`src/input.py`'s X11 path), test on
  an actual X11 session where possible - see [LINUX_GUIDE.md](LINUX_GUIDE.md).

CI (`.github/workflows/ci.yml`) runs the same test suite on Windows and Linux
for every push/PR, and builds a standalone GUI executable (via
`scripts/build_exe.py`) for Windows, Linux, and macOS whenever a `vX.Y.Z` tag
is pushed.

## Versioning

Every user-facing change should bump [`VERSION.md`](VERSION.md) and add a
matching entry to [`CHANGELOG.md`](CHANGELOG.md) in the same PR, following
[Semantic Versioning](https://semver.org/): MAJOR for breaking config-format/
behavior changes, MINOR for backward-compatible feature additions, PATCH for
fixes. Small non-user-facing changes (typo fixes, comments) don't need a bump.

## Adding a game profile

Profiles live in a separate repo: open a pull request on
[TIGHC/Profiles](https://github.com/TIGHC/Profiles) instead, or use the
GUI's Profiles tab -> "New profile...".

## Reporting a bug

Open an issue with your OS, what you expected vs. what happened, and (if
relevant) which profile/game and what's in the Run tab's log at the time.

## License

TIGHC is licensed under the [GPL-3.0-or-later](LICENSE.md). By contributing,
you agree your contribution is licensed under the same terms.
