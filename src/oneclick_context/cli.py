from pathlib import Path
import typer
from .core import build_tree
from .exporters import text, markdown, json as jsonexp, html

app = typer.Typer(add_completion=False)

FMT_MAP = {
    "text": lambda t, p: "\n".join(text.render(t)),
    "md": markdown.render_md,
    "json": lambda t, p: jsonexp.render_json(t),
    "html": lambda t, p: html.render_html(t),
}

@app.command()
def main(
    path: Path = typer.Argument(".", help="Folder to scan"),
    depth: int = typer.Option(3, "--depth", "-d"),
    fmt: str = typer.Option("text", "--fmt", "-f", help="text|md|json|html"),
):
    tree_obj = build_tree(path, max_depth=depth)
    try:
        output = FMT_MAP[fmt](tree_obj, path)
    except KeyError:
        typer.echo(f"Unknown format '{fmt}'", err=True)
        raise typer.Exit(1)
    typer.echo(output)

if __name__ == "__main__":
    app()
