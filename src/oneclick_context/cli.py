# src/oneclick_context/cli.py
from pathlib import Path
import sys
import typer

from .tree import list_tree        # your existing function
from .render_md import render_md   # we'll create right below

app = typer.Typer(
    add_completion=False,
    help="One-Click Context Toolkit – visual file trees & summaries",
)

@app.command()
def main(
    path: Path = typer.Argument(".", help="Folder to scan"),
    depth: int = typer.Option(2, "--depth", "-d", help="Max folder depth"),
    fmt: str = typer.Option(
        "text", "--fmt", "-f", help="Output format: text | md"
    ),
):
    """Generate a file-tree context digest."""
    # Safety: ensure path exists
    if not path.exists():
        typer.secho(f"[error] Path not found: {path}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Build the raw tree string with your current function
    tree_str = list_tree(str(path), depth=depth, return_str=True)

    # Decide how to output
    if fmt == "text":
        typer.echo(tree_str)
    elif fmt == "md":
        typer.echo(render_md(tree_str, path))
    else:
        typer.secho(f"Unknown --fmt '{fmt}'", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
