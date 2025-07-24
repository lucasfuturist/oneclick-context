from pathlib import Path
from typing import List, Optional

import typer
import questionary as q

from .core import build_tree
from .exporters import text, markdown, json as jsonexp, html

# ── Typer setup ───────────────────────────────────────────────────────────────
app = typer.Typer(add_completion=False, help="One-Click Context Toolkit")

FMT_MAP = {
    "text": lambda t, p: "\n".join(text.render(t)),
    "md":   markdown.render_md,
    "json": lambda t, p: jsonexp.render_json(t),
    "html": lambda t, p: html.render_html(t),
}

COMMON_LIBS = ["node_modules", "dist", ".venv", ".git", "__pycache__"]

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Helper functions                                                          │
# ╰────────────────────────────────────────────────────────────────────────────╯
def sanitize_path(raw: str) -> Path:
    return Path(raw.strip().lstrip("./").strip('"')).expanduser().resolve()

def ask_generation_params(
    default_path: Path,
    default_depth: int,
    default_fmt: str,
) -> dict:
    """Prompt the classic wizard questions and return a kwargs dict."""
    raw = q.text("🔹 Folder to scan", default=str(default_path)).ask()
    scan_path = sanitize_path(raw)

    depth = int(q.text("🔹 Max depth", default=str(default_depth)).ask())

    suppress: list[str] = []
    if q.confirm("🔹 Skip common library folders?", default=True).ask():
        suppress += COMMON_LIBS

    extra_sup = q.text("🔹 Extra folders to suppress (comma-sep)", default="").ask()
    if extra_sup:
        suppress += [s.strip() for s in extra_sup.split(",") if s.strip()]

    list_scripts: list[str] = []
    if q.confirm("🔹 Print full source of scripts?", default=False).ask():
        exts = q.text("   Extensions (space-sep)", default=".py .ts").ask()
        list_scripts = exts.split()

    fmt = q.select(
        "🔹 Output format", choices=["text", "md", "json", "html"], default=default_fmt
    ).ask()

    return dict(
        path=scan_path,
        depth=depth,
        fmt=fmt,
        suppress=suppress,
        list_scripts=list_scripts,
    )

def generate_and_output(
    *,
    params: dict,
    save_dir: Optional[Path] = None,
) -> None:
    """Build tree, render, and either print or write to file."""
    # safety
    dangers = [
        d
        for d in COMMON_LIBS
        if (params["path"] / d).is_dir()
        and d.lower() not in {s.lower() for s in params["suppress"]}
    ]
    if dangers:
        typer.secho(
            f"⚠️  Detected large folders {dangers}. Consider suppressing them.",
            fg=typer.colors.YELLOW,
        )

    # build & render
    tree_obj = build_tree(
        params["path"], max_depth=params["depth"], suppress=params["suppress"]
    )
    output = FMT_MAP[params["fmt"]](tree_obj, params["path"])

    # decide destination
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        ext = "md" if params["fmt"] == "md" else params["fmt"]
        outfile = save_dir / f"tree.{ext}"
        outfile.write_text(output, encoding="utf-8")
        typer.secho(f"📁 Saved to: {outfile}", fg=typer.colors.GREEN, hyperlink=outfile.as_uri())
    else:
        typer.echo(output)

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Typer command                                                             │
# ╰────────────────────────────────────────────────────────────────────────────╯
@app.command()
def main(
    path: Path = typer.Argument(".", help="Folder to scan"),
    depth: int = typer.Option(3, "--depth", "-d"),
    fmt: str = typer.Option("text", "--fmt", "-f", help="text|md|json|html"),
    suppress: List[str] = typer.Option([], "--suppress", "-s"),
    list_scripts: List[str] = typer.Option([], "--list-scripts", "-l"),
    guide: bool = typer.Option(False, "--guide", "-g", help="One-shot wizard"),
    menu: bool = typer.Option(False, "--menu", "-m", help="Interactive menu session"),
):
    # ── Menu mode ────────────────────────────────────────────────────────────
    if menu:
        save_dir: Optional[Path] = None
        while True:
            choice = q.select(
                "📜  Main menu",
                choices=[
                    f"Set save location (currently: {save_dir if save_dir else 'OFF'})",
                    "Generate tree",
                    "Exit",
                ],
            ).ask()

            if choice.startswith("Set save"):
                raw = q.path("💾  Folder for saved trees (leave blank to disable)").ask()
                save_dir = sanitize_path(raw) if raw else None
                typer.secho(
                    f"✔ Save location set to: {save_dir}" if save_dir else "✖ Auto-save disabled",
                    fg=typer.colors.GREEN,
                )
            elif choice == "Generate tree":
                params = ask_generation_params(path, depth, fmt)
                generate_and_output(params=params, save_dir=save_dir)
            else:
                raise typer.Exit()

    # ── Guide (one-shot wizard) ──────────────────────────────────────────────
    if guide:
        params = ask_generation_params(path, depth, fmt)
        # ask where to save for *this* run
        save_raw = q.text("💾  File name to save (blank = auto-name / stdout)", default="").ask()
        if save_raw:
            save_path = sanitize_path(save_raw)
        else:
            stamp =  Path(params['path']).name + "_" +  \
                    typer.datetime.now().strftime("%Y-%m-%d_%H-%M")
            ext   = params["fmt"] if params["fmt"] != "md" else "md"
            save_path = Path.cwd() / f"{stamp}.{ext}"
        save_dir = save_path.parent if save_raw or q.confirm("Save to file?", default=False).ask() else None
        generate_and_output(params=params, save_dir=save_dir)
        raise typer.Exit()

    # ── Flag-driven fast path ────────────────────────────────────────────────
    generate_and_output(
        params=dict(
            path=path,
            depth=depth,
            fmt=fmt,
            suppress=suppress,
            list_scripts=list_scripts,
        ),
        save_dir=None,
    )

if __name__ == "__main__":
    app()
