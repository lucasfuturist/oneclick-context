from pathlib import Path
from typing import List

import questionary as q
import typer

from .utils import sanitize_path, _abort_if_none, COMMON_LIBS

def ask_generation_params(
    default_path: Path,
    default_depth: int,
    default_fmt: str,
) -> dict:
    """Interactive wizard → returns dict used by renderer."""
    raw = _abort_if_none(
        q.text("🔹 Folder to scan", default=str(default_path)).ask()
    )
    scan_path = sanitize_path(raw)

    depth_raw = _abort_if_none(
        q.text("🔹 Max depth", default=str(default_depth)).ask()
    )
    depth = int(depth_raw)

    suppress: List[str] = []
    if q.confirm("🔹 Skip common library folders?", default=True).ask():
        suppress += COMMON_LIBS

    extra = q.text("🔹 Extra folders to suppress (comma-sep)", default="").ask()
    if extra:
        suppress += [s.strip() for s in extra.split(",") if s.strip()]

    list_scripts: List[str] = []
    if q.confirm("🔹 Print full source of scripts?", default=False).ask():
        exts = q.text("   Extensions (space-sep)", default=".py .ts").ask()
        list_scripts = exts.split()

    fmt = q.select(
        "🔹 Output format",
        choices=["text", "md", "json", "html"],
        default=default_fmt,
    ).ask()

    return dict(
        path=scan_path,
        depth=depth,
        fmt=fmt,
        suppress=suppress,
        list_scripts=list_scripts,
    )
