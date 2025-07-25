# Standard library imports
import sys
from pathlib import Path
from typing import Optional, List

# Third-party imports
import typer
import click as _click

# --- Compatibility shim: allow make_metavar() to be called without ctx ---
if not getattr(_click.core.Parameter, "_oc_ctx_shimmed", False):
    _orig_make_metavar = _click.core.Parameter.make_metavar
    def _compat_make_metavar(self, ctx=None):
        return _orig_make_metavar(self, ctx)
    _click.core.Parameter.make_metavar = _compat_make_metavar
    _click.core.Parameter._oc_ctx_shimmed = True
# ------------------------------------------------------------------------

# First-party imports
from .commands.generate import generate_output
from .prompts import run_guide, run_menu

app = typer.Typer(help="Generate compact, navigable file trees with optional inlined source code.")

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    path: str = typer.Option(".", "--path", "-p", help="The root folder to scan."),
    depth: int = typer.Option(3, "--depth", "-d", help="Max recursion depth.", show_default=True),
    languages: List[str] = typer.Option(
        (), "--lang", "-l",
        help="Filter tree to only include these extensions (repeatable).",
        show_default="(all files)"
    ),
    inline: List[str] = typer.Option(
        (), "--inline", "-i",
        help="Extensions of scripts to print in full (repeatable).",
        show_default="(none)"
    ),
    fmt: str = typer.Option(
        "text", "--format", "--fmt", "-f",
        case_sensitive=False, help="Output format."
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o",
        help="Write result to a file instead of stdout.",
        show_default="(prints to console)"
    ),
    guide: bool = typer.Option(False, "--guide", "-g", help="Run the interactive step-by-step wizard."),
    menu: bool = typer.Option(False, "--menu", "-m", help="Run the persistent interactive menu."),
) -> None:
    """
    One-Click Context: Generate a project tree with inlined source code.
    """
    output_path = Path(output).expanduser().resolve() if output else None

    if guide or menu:
        (run_guide if guide else run_menu)(
            default_root=Path(path),
            default_depth=depth,
            default_format=fmt,
            default_output=output_path,
        )
        return

    if ctx.invoked_subcommand is None:
        generate_output(
            root=Path(path),
            depth=depth,
            fmt=fmt,
            output_path=output_path,
            languages=tuple(languages),
            inline_exts=tuple(inline)
        )
