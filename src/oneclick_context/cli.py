from pathlib import Path
from typing import List, Optional

import typer
import questionary as q

from .prompts import ask_generation_params
from .renderer import generate_and_output
from .utils import sanitize_path

# â”€â”€ Cheat-sheet shown by oneclick help / --help â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
QUICK_REF = r"""
â”Œâ”€ One-Click Context Toolkit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
| Generate a project tree (and optionally inline script source).     |
|                                                                    |
|  BASIC                                                             |
|  -----                                                             |
|  oneclick <folder>               # text tree of <folder>           |
|  oneclick -f md                  # Markdown output                 |
|  oneclick -f json                # JSON (for tooling)              |
|  oneclick -f html                # self-contained HTML             |
|                                                                    |
|  COMMON FLAGS                                                       |
|  ------------                                                       |
|  -d, --depth N              descend N levels  (default 3)          |
|  -s, --suppress DIR [...]    skip dirs (repeatable)                |
|  -l, --list-scripts EXT [...] inline source for *.EXT files        |
|  -o, --output FILE          write result to FILE instead of stdout |
|                                                                    |
|  INTERACTIVE MODES                                                  |
|  -----------------                                                  |
|  -g, --guide              step-by-step wizard (single run)         |
|  -m, --menu               stay in menu session (generate many)     |
|                                                                    |
|  EXAMPLES                                                           |
|  --------                                                           |
|  oneclick src -d 2 -f md                                           |
|  oneclick . -f json -s node_modules -s dist                        |
|  oneclick . -l .py -l .ts -o tree.txt                              |
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
"""

# â”€â”€ Typer app (with default --help disabled) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
app = typer.Typer(add_completion=False,
                  add_help_option=False,
                  help="One-Click Context Toolkit")

# â”€â”€ main / default command â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.command()
def main(
    path: Path = typer.Argument(".", help="Folder to scan"),
    depth: int = typer.Option(3, "--depth", "-d"),
    fmt: str = typer.Option("text", "--fmt", "-f", help="text|md|json|html"),
    suppress: List[str] = typer.Option([], "--suppress", "-s"),
    list_scripts: List[str] = typer.Option([], "--list-scripts", "-l"),
    guide: bool = typer.Option(False, "--guide", "-g", help="One-shot wizard"),
    menu: bool  = typer.Option(False, "--menu", "-m", help="Interactive menu"),
    help_flag: bool = typer.Option(False, "--help", "-h",
        help="Show quick reference and exit"),
):
    # quick reference
    if help_flag:
        typer.echo(QUICK_REF)
        raise typer.Exit()

    # â”€â”€ Menu session â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if menu:
        save_dir: Optional[Path] = Path.cwd().parent.resolve()
        while True:
            choice = q.select(
                "ðŸ“œ  Main menu",
                choices=[
                    f"Set save location (currently: {save_dir if save_dir else 'OFF'})",
                    "Generate tree",
                    "Exit",
                ],
            ).ask()

            if choice.startswith("Set save"):
                prompt = "ðŸ’¾  Folder for saved trees (Enter = keep; off = disable)"
                raw = q.path(prompt, default=str(save_dir) if save_dir else "").ask()
                if raw is None:
                    continue
                raw = raw.strip()
                if raw.lower() in {"off", "disable", "none"}:
                    save_dir = None
                elif raw:
                    save_dir = sanitize_path(raw)
                typer.secho(
                    f"âœ” Save location set to: {save_dir}"
                    if save_dir else "âœ– Auto-save disabled",
                    fg=typer.colors.GREEN,
                )

            elif choice == "Generate tree":
                params = ask_generation_params(path, depth, fmt)
                generate_and_output(params=params, save_dir=save_dir)
            else:
                raise typer.Exit()

    # â”€â”€ Guide (one-shot wizard) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if guide:
        params = ask_generation_params(path, depth, fmt)
        out_raw = q.text("ðŸ’¾  File name (blank = stdout)", default="").ask()
        save_dir = Path(out_raw).parent if out_raw else None
        generate_and_output(params=params, save_dir=save_dir)
        raise typer.Exit()

    # â”€â”€ Flag mode (no interaction) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

# â”€â”€ quick-reference sub-command â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.command("help")
def _print_help():
    """Display quick reference cheat-sheet."""
    typer.echo(QUICK_REF)

# â”€â”€ scripts sub-command â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€@app.command("scripts")
def _list_scripts(
    extension: str = typer.Argument(..., help="Extension like .py"),
    folder: Path  = typer.Argument(".", help="Folder to scan"),
    suppress: List[str] = typer.Option([], "--suppress", "-s",
        help="Folders to skip (repeatable)"),
    out_file: Optional[Path] = typer.Option(None, "--out", "-o",
        help="Concatenate full source of every match into this file"),
):
    """
    Recursively list every file whose suffix == *extension*.
    With --out, writes a single file containing the full source of
    every match, separated by Markdown-style headers.
    """
    ext = extension if extension.startswith(".") else f".{extension}"
    suppress_lc = {s.lower() for s in suppress}

    matches: list[Path] = [
        p for p in folder.rglob(f"*{ext}")
        if p.is_file() and all(part.lower() not in suppress_lc for part in p.parts)
    ]

    if out_file:
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with out_file.open("w", encoding="utf-8") as fh:
            for idx, p in enumerate(matches, 1):
                try:
                    rel = p.relative_to(folder.resolve())
                except ValueError:
                    rel = p
                header = f"\\n\\n### {idx}. `{rel}`\\n---\\n"
                fh.write(header)
                fh.write(p.read_text(encoding="utf-8", errors="replace"))
        typer.secho(f"📄 Wrote {len(matches)} files → {out_file}",
                    fg=typer.colors.GREEN)
    else:
        base = folder.resolve()
        for p in matches:
            try:
                typer.echo(p.relative_to(base))
            except ValueError:
                typer.echo(p)
\nif __name__ == "__main__":
    app()





