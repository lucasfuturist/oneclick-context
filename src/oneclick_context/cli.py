from pathlib import Path
from typing import List
import typer
import questionary as q

from .core import build_tree
from .exporters import text, markdown, json as jsonexp, html

app = typer.Typer(add_completion=False, help="One-Click Context Toolkit")

FMT_MAP = {
    "text": lambda t, p: "\n".join(text.render(t)),
    "md":   markdown.render_md,
    "json": lambda t, p: jsonexp.render_json(t),
    "html": lambda t, p: html.render_html(t),
}

COMMON_LIBS = ["node_modules", "dist", ".venv", ".git", "__pycache__"]

@app.command()
def main(
    path: Path = typer.Argument(".", help="Folder to scan"),
    depth: int = typer.Option(3, "--depth", "-d"),
    fmt: str = typer.Option("text", "--fmt", "-f", help="text|md|json|html"),
    suppress: List[str] = typer.Option([], "--suppress", "-s"),
    list_scripts: List[str] = typer.Option([], "--list-scripts", "-l"),
    guide: bool = typer.Option(False, "--guide", "-g", help="Interactive wizard"),
):
    # ── Guide mode ─────────────────────────────────────────────────────────────
    if guide:
        typer.secho("┌─ One-Click Context Guide ────────────────────────────", fg="cyan")
        path = Path(q.text("🔹 Folder to scan", default=str(path)).ask())
        depth = int(q.text("🔹 Max depth", default=str(depth)).ask())

        if q.confirm("🔹 Skip common library folders?", default=True).ask():
            suppress += COMMON_LIBS

        extra_sup = q.text(
            "🔹 Extra folders to suppress (comma-sep)", default=""
        ).ask()
        if extra_sup:
            suppress += [s.strip() for s in extra_sup.split(",") if s.strip()]

        if q.confirm("🔹 Print full source of scripts?", default=False).ask():
            exts = q.text("   Extensions (space-sep)", default=".py .ts").ask()
            list_scripts = exts.split()

        fmt = q.select("🔹 Output format", choices=["text", "md", "json", "html"], default=fmt).ask()
        typer.secho("└─────────────────────────────────────────────────────\n", fg="cyan")

    # ── Safety warning for large libs ──────────────────────────────────────────
    dangers = [d for d in COMMON_LIBS if (path / d).is_dir() and d.lower() not in {s.lower() for s in suppress}]
    if dangers:
        typer.secho(
            f"⚠️  Detected large folders {dangers}. Use --suppress or --guide to skip them.",
            fg=typer.colors.YELLOW,
        )

    # ── Build & render tree ────────────────────────────────────────────────────
    tree_obj = build_tree(path, max_depth=depth, suppress=suppress)
    try:
        output = FMT_MAP[fmt](tree_obj, path)
    except KeyError:
        typer.echo(f"Unknown format '{fmt}'", err=True)
        raise typer.Exit(1)

    typer.echo(output)

if __name__ == "__main__":
    app()
