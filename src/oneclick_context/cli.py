# Standard library imports
from pathlib import Path
from typing import Optional, List

# Third-party imports
import typer

# First-party imports
from .commands.generate import generate_output
from .prompts import run_guide, run_menu

app = typer.Typer(add_completion=False, help="Generate compact file trees")

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    path: str = typer.Option(".", "--path", "-p", help="The root folder to scan."),
    depth: int = typer.Option(3, "--depth", "-d", show_default=True),
    languages: List[str] = typer.Option(
        (), "--lang", "-l", help="Filter tree to only include these extensions."
    ),
    inline: List[str] = typer.Option(
        (), "--inline", "-i", help="Extensions of scripts to print in full, e.g., .py"
    ),
    fmt: str = typer.Option(
        "text", "--format", "--fmt", "-f",
        case_sensitive=False, help="output format"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="write result to FILE instead of stdout",
        dir_okay=False,
    ),
    guide: bool = typer.Option(False, "--guide", "-g", help="step-by-step wizard"),
    menu: bool = typer.Option(False, "--menu", "-m", help="interactive menu"),
) -> None:
    """Entry point that delegates to command modules."""
    if guide or menu:
        (run_guide if guide else run_menu)(
            default_root=Path(path),
            default_depth=depth,
            default_format=fmt,
            default_output=output,
        )
        return

    if ctx.invoked_subcommand is None:
        generate_output(
            root=Path(path),
            depth=depth,
            fmt=fmt,
            output_path=output,
            languages=tuple(languages),
            inline_exts=tuple(inline)
        )
