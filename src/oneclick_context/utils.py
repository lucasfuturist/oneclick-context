from pathlib import Path
from typing import Optional
import inspect, click, typer

COMMON_LIBS = ["node_modules", "dist", ".venv", ".git", "__pycache__"]

def _abort_if_none(val):
    """Exit CLI (code 0) when Questionary returns None (Esc / Ctrl-C)."""
    if val is None:
        raise typer.Exit()
    return val

def sanitize_path(raw: Optional[str]) -> Path:
    """
    Return absolute Path from user input.
    If *raw* is None/blank → current working directory.
    """
    if raw is None or not str(raw).strip():
        return Path.cwd()
    return (
        Path(str(raw).strip().lstrip("./").strip('"'))
        .expanduser()
        .resolve()
    )

def discover_extensions(root: Path, suppress: list[str]) -> list[str]:
    """
    Return a sorted list of unique file suffixes ('.py', '.ts', …)
    under *root*, skipping suppressed directories.
    """
    suppress_lc = {s.lower() for s in suppress}
    exts: set[str] = set()
    for p in root.rglob("*"):
        if not p.is_file() or not p.suffix:
            continue
        if any(part.lower() in suppress_lc for part in p.parts):
            continue
        exts.add(p.suffix)
    return sorted(exts, key=str.lower)


SUPPORTS_HYPERLINK = "hyperlink" in inspect.signature(click.style).parameters
