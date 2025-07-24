from pathlib import Path
from typing import List

import questionary as q
import typer

from .utils import (
    sanitize_path,
    _abort_if_none,
    COMMON_LIBS,
    discover_extensions,
)


def ask_generation_params(
    default_path: Path,
    default_depth: int,
    default_fmt: str,
) -> dict:
    """Interactive wizard → returns dict used by renderer."""
    # ── folder prompt ───────────────────────────────────────────────
    raw = _abort_if_none(
        q.text("🔹 Folder to scan", default=str(default_path)).ask()
    )
    scan_path = sanitize_path(raw)

    # ── depth prompt ────────────────────────────────────────────────
    depth_raw = _abort_if_none(
        q.text("🔹 Max depth", default=str(default_depth)).ask()
    )
    depth = int(depth_raw)

    # ── suppress rules ──────────────────────────────────────────────
    suppress: List[str] = []
    if q.confirm("🔹 Skip common library folders?", default=True).ask():
        suppress += COMMON_LIBS

    extra = q.text("🔹 Extra folders to suppress (comma-sep)", default="").ask()
    if extra:
        suppress += [s.strip() for s in extra.split(",") if s.strip()]

    # ── script-source options ───────────────────────────────────────
    list_scripts: List[str] = []
    if q.confirm("🔹 Print full source of scripts?", default=False).ask():
        found = discover_extensions(scan_path, suppress)
        if not found:                       # fallback when none discovered
            found = [".py", ".ts"]

        picked = q.checkbox(
            "   Select extensions (space to toggle)",
            choices=found,
            default=[".py"] if ".py" in found else found[:1],
        ).ask()

        list_scripts = picked or []

    # ── output format ───────────────────────────────────────────────
    fmt = q.select(
        "🔹 Output format",
        choices=["text", "md", "json", "html"],
        default=default_fmt,
    ).ask()

    # ── return parameters ───────────────────────────────────────────
    return dict(
        path=scan_path,
        depth=depth,
        fmt=fmt,
        suppress=suppress,
        list_scripts=list_scripts,
    )
