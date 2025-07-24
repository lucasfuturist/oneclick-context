from pathlib import Path
from typing import Optional

import typer

from .core import build_tree
from .exporters import text, markdown, json as jsonexp, html
from .utils import COMMON_LIBS, SUPPORTS_HYPERLINK

FMT_MAP = {
    "text": lambda t, p: "\n".join(text.render(t)),
    "md":   markdown.render_md,
    "json": lambda t, p: jsonexp.render_json(t),
    "html": lambda t, p: html.render_html(t),
}

def generate_and_output(
    *,
    params: dict,
    save_dir: Optional[Path] = None,
) -> None:
    """Build tree, render, and print or save."""
    # warn on big dirs
    dangers = [
        d for d in COMMON_LIBS
        if (params["path"] / d).is_dir()
        and d.lower() not in {s.lower() for s in params["suppress"]}
    ]
    if dangers:
        typer.secho(
            f"⚠️  Detected large folders {dangers}. Consider suppressing them.",
            fg=typer.colors.YELLOW,
        )

    tree = build_tree(
        params["path"],
        max_depth=params["depth"],
        suppress=params["suppress"],
    )
    output = FMT_MAP[params["fmt"]](tree, params["path"])

    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        ext = "md" if params["fmt"] == "md" else params["fmt"]
        outfile = save_dir / f"tree.{ext}"
        outfile.write_text(output, encoding="utf-8")

        kw = dict(fg=typer.colors.GREEN)
        if SUPPORTS_HYPERLINK:
            kw["hyperlink"] = outfile.as_uri()
        typer.secho(f"📁 Saved to: {outfile}", **kw)
    else:
        typer.echo(output)
