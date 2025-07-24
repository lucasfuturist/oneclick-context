"""
Generate a directory tree and send it to stdout or a file.

This module is intentionally free of any CLI/Typer imports so it can be
unit-tested or called from other code without side effects.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from rich.console import Console

from ..core import build_tree
from ..exporters import text, markdown, json as jsonexp, html

FMT_MAP = {
    "text": lambda t, p: "\n".join(text.render(t)),
    "md": markdown.render_md,
    "json": lambda t, p: jsonexp.render_json(t),
    "html": lambda t, p: html.render_html(t),
}

console = Console()


def generate_output(
    root: Path,
    depth: int,
    fmt: str,
    output_path: Optional[Path] = None,
    languages: Tuple[str, ...] = (),
) -> None:
    """Build the tree and render it in the requested format."""
    tree = build_tree(
        root,
        max_depth=depth,
        extra_exts=list(languages),
    )
    rendered = FMT_MAP[fmt.lower()](tree, root)

    if output_path:
        dst = output_path.expanduser().resolve()
        dst.write_text(rendered, encoding="utf-8")
        console.print(f"[green]✓ Saved to {dst}[/]")
    else:
        print(rendered)
