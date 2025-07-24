# Changelog

All notable changes to this project will be documented in this file.

## [0.2.2] - 2025-07-24

### Changed
- Major refactor of the CLI to be a thin entry point (`cli.py`) that delegates logic to a new `commands` module.
- The `path` argument is now a named option (`--path` / `-p`) to work around a library bug on Python 3.13.
- The test suite now uses `typer.testing.CliRunner` for more robust, environment-independent testing.

### Fixed
- Fixed a critical bug where the `--output / -o` flag was advertised but not implemented.
- Fixed a series of `TypeError` crashes on Python 3.13 caused by `typer`'s handling of `Path` and `Tuple` type hints.

### Removed
- Deleted the redundant, legacy CLI script `tree.py`.
- Deleted duplicate modules `ext_finder.py` and `render_md.py`.
- Removed the now-unused `renderer.py` module after refactoring.
