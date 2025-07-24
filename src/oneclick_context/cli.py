from pathlib import Path
from typing import List, Optional

import typer
import questionary as q

from .prompts import ask_generation_params
from .renderer import generate_and_output
from .utils import sanitize_path

QUICK_REF = r"""
┌─ One-Click Context Toolkit ─────────────────────────────────────────┐
| Generate a project tree (and optionally inline script source).     |
|                                                                    |
|  Basic                                                             |
|  -----                                                             |
|  oneclick <folder>               # print text tree of <folder>     |
|  oneclick -f md                  # markdown output                 |
|  oneclick -f json                # JSON (for tooling)              |
|  oneclick -f html                # self-contained HTML             |
|                                                                    |
|  Common flags                                                      |
|  ------------                                                      |
|  -d, --depth N              descend N levels   (default 3)         |
|  -s, --suppress DIR [...]    skip dirs (repeatable)                |
|  -l, --list-scripts EXT [...] inline source for *.EXT files        |
|  -o, --output FILE           write to FILE instead of stdout       |
|                                                                    |
|  Interactive helpers                                               |
|  --------------------                                              |
|  -g, --guide              step-by-step wizard (single run)         |
|  -m, --menu               stay in a menu session (can run many)    |
|                                                                    |
|  Examples                                                          |
|  --------                                                          |
|  oneclick src -d 2 -f md                                           |
|  oneclick ./project -f json -s node_modules -s dist               |
|  oneclick . -l .py -l .ts -o tree.txt                              |
└────────────────────────────────────────────────────────────────────┘
"""

app = typer.Typer(add_completion=False, help="One-Click Context Toolkit")

# ── COMMAND ───────────────────────────────────────────────────────────
@app.command()
def main(
    path: Path = typer.Argument(".", help="Folder to scan"),
    depth: int = typer.Option(3, "--depth", "-d"),
    fmt: str = typer.Option("text", "--fmt", "-f", help="text|md|json|html"),
    suppress: List[str] = typer.Option([], "--suppress", "-s"),
    list_scripts: List[str] = typer.Option([], "--list-scripts", "-l"),
    guide: bool = typer.Option(False, "--guide", "-g", help="One-shot wizard"),
    menu: bool = typer.Option(False, "--menu", "-m", help="Interactive menu"),
):
    # ── Menu mode ─────────────────────────────────────────────────────
    if menu:
        save_dir: Optional[Path] = Path.cwd().parent.resolve()
        while True:
            choice = q.select(
                "📜  Main menu",
                choices=[
                    f"Set save location (currently: {save_dir if save_dir else 'OFF'})",
                    "Generate tree",
                    "Exit",
                ],
            ).ask()

            # ---- set save dir ----
            if choice.startswith("Set save"):
                prompt = "💾  Folder for saved trees (Enter = keep; off = disable)"
                raw = q.path(prompt, default=str(save_dir) if save_dir else "").ask()
                if raw is None:
                    continue
                raw = raw.strip()
                if raw.lower() in {"off", "disable", "none"}:
                    save_dir = None
                elif raw:  # non-empty string
                    save_dir = sanitize_path(raw)
                typer.secho(
                    f"✔ Save location set to: {save_dir}"
                    if save_dir else "✖ Auto-save disabled",
                    fg=typer.colors.GREEN,
                )
            # ---- generate ----
            elif choice == "Generate tree":
                params = ask_generation_params(path, depth, fmt)
                generate_and_output(params=params, save_dir=save_dir)
            else:
                raise typer.Exit()

    # ── Guide mode ────────────────────────────────────────────────────
    if guide:
        params = ask_generation_params(path, depth, fmt)
        out_raw = q.text("💾  File name (blank = stdout)", default="").ask()
        save_dir = Path(out_raw).parent if out_raw else None
        generate_and_output(params=params, save_dir=save_dir)
        raise typer.Exit()

    # ── Flag mode ────────────────────────────────────────────────────
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

@app.command("help")
def _print_help():
    """Display quick reference cheat-sheet."""
    import typer  # local import to avoid cycles
    typer.echo(QUICK_REF)
