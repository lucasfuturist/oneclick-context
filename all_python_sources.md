\n\n### 1. `tests\test_cli.py`\n---\n﻿from subprocess import run, PIPE
from pathlib import Path

def test_json_output(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.txt").write_text("x")
    result = run(["oneclick", str(tmp_path), "--fmt", "json"], stdout=PIPE, text=True)
    assert result.returncode == 0
    assert '"a.txt"' in result.stdout
\n\n### 2. `tests\test_smoke.py`\n---\n﻿def test_smoke():
    assert True
\n\n### 3. `tests\__init__.py`\n---\n\n\n### 4. `src\oneclick_context\cli.py`\n---\n﻿from pathlib import Path
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

# â”€â”€ scripts sub-command â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.command("scripts")
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
if __name__ == "__main__":
    app()





\n\n### 5. `src\oneclick_context\core.py`\n---\n﻿from pathlib import Path
from typing import TypedDict, List

class Node(TypedDict):
    type: str         # "file" | "dir"
    name: str
    children: List["Node"]

def build_tree(
    root: Path,
    *,
    max_depth: int = 3,
    suppress: list[str] | None = None,
    _depth: int = 0,
) -> Node:
    suppress = {s.lower() for s in (suppress or [])}
    node: Node = {"type": "dir", "name": root.name, "children": []}

    if _depth >= max_depth:
        return node

    try:
        entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return node

    for entry in entries:
        if entry.is_dir() and entry.name.lower() in suppress:
            continue
        if entry.is_dir():
            node["children"].append(
                build_tree(entry, max_depth=max_depth, suppress=suppress, _depth=_depth + 1)
            )
        else:
            node["children"].append({"type": "file", "name": entry.name, "children": []})
    return node
\n\n### 6. `src\oneclick_context\ext_finder.py`\n---\n﻿from pathlib import Path
from typing import List

def discover_extensions(root: Path, suppress: List[str] | None = None) -> list[str]:
    """
    Return sorted unique file suffixes ('.py', '.ts', ...) under *root*,
    skipping any directories in *suppress*.
    """
    suppress_lc = {s.lower() for s in suppress or []}
    exts: set[str] = set()
    for p in root.rglob("*"):
        if p.is_file() and p.suffix:
            if any(part.lower() in suppress_lc for part in p.parts):
                continue
            exts.add(p.suffix)
    return sorted(exts, key=str.lower)
\n\n### 7. `src\oneclick_context\prompts.py`\n---\n﻿from pathlib import Path
from typing import List

import questionary as q
import typer

from .utils import (
    sanitize_path,
    _abort_if_none,
    COMMON_LIBS,
)
from .ext_finder import discover_extensions


def ask_generation_params(
    default_path: Path,
    default_depth: int,
    default_fmt: str,
) -> dict:
    """Interactive wizard → returns dict used by renderer."""

    # ── folder ─────────────────────────────────────────────────────
    raw = _abort_if_none(
        q.text("🔹 Folder to scan", default=str(default_path)).ask()
    )
    scan_path = sanitize_path(raw)

    # ── depth ──────────────────────────────────────────────────────
    depth_raw = _abort_if_none(
        q.text("🔹 Max depth", default=str(default_depth)).ask()
    )
    depth = int(depth_raw)

    # ── suppress rules ────────────────────────────────────────────
    suppress: List[str] = []
    if q.confirm("🔹 Skip common library folders?", default=True).ask():
        suppress += COMMON_LIBS

    extra = q.text("🔹 Extra folders to suppress (comma-sep)", default="").ask()
    if extra:
        suppress += [s.strip() for s in extra.split(",") if s.strip()]

    # ── script-source options ─────────────────────────────────────
    list_scripts: List[str] = []
    if q.confirm("🔹 Print full source of scripts?", default=False).ask():
        found = discover_extensions(scan_path, suppress)
        if not found:
            found = [".py", ".ts"]

        # ︙ convert suffixes → Choice objects so default validates
        choices = [q.Choice(title=sfx, value=sfx) for sfx in found]
        default_sel = ".py" if ".py" in found else found[0]

        picked = q.checkbox(
            "   Select extensions (space to toggle)",
            choices=choices,
            default=[default_sel],
        ).ask()

        list_scripts = picked or []

    # ── output format ─────────────────────────────────────────────
    fmt = q.select(
        "🔹 Output format",
        choices=["text", "md", "json", "html"],
        default=default_fmt,
    ).ask()

    # ── return params ─────────────────────────────────────────────
    return dict(
        path=scan_path,
        depth=depth,
        fmt=fmt,
        suppress=suppress,
        list_scripts=list_scripts,
    )
\n\n### 8. `src\oneclick_context\renderer.py`\n---\n﻿from pathlib import Path
from typing import Optional

import typer

from .core import build_tree
from .tree import list_scripts
from .exporters import text, markdown, json as jsonexp, html
from .utils import COMMON_LIBS, SUPPORTS_HYPERLINK

FMT_MAP = {
    "text": lambda t, p: "\n".join(text.render(t)),
    "md":   markdown.render_md,
    "json": lambda t, p: jsonexp.render_json(t),
    "html": lambda t, p: html.render_html(t),
}


def generate_and_output(
    *, params: dict, save_dir: Optional[Path] = None,
) -> None:
    """Build tree, render, and print or save."""
    # warn on big dirs
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

    tree = build_tree(
        params["path"],
        max_depth=params["depth"],
        suppress=params["suppress"],
    )
    output = FMT_MAP[params["fmt"]](tree, params["path"])

    # ── inject full script sources (text / md only) ───────────────────
    if params["list_scripts"] and params["fmt"] in {"text", "md"}:
        out_lines = output.splitlines()
        list_scripts(
            params["path"],
            params["list_scripts"],
            params["suppress"],
            out_lines,
            quiet=True,
        )
        output = "\n".join(out_lines)
    # ──────────────────────────────────────────────────────────────────

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
\n\n### 9. `src\oneclick_context\render_md.py`\n---\n"""
Markdown renderer for the One-Click Context Toolkit.

Wraps a plain-text tree in collapsible <details> so it’s paste-ready
for GitHub, LinkedIn, etc.
"""

from pathlib import Path

def render_md(tree_str: str, folder: Path | str) -> str:
    # Resolve "." → current working directory name
    p = Path(folder).resolve()
    name = p.name if p.name else p.parent.name or str(p)
    return (
        f"<details><summary>📁 {name}</summary>\n\n"
        "```text\n"
        f"{tree_str.rstrip()}\n"
        "```\n"
        "</details>"
    )
\n\n### 10. `src\oneclick_context\tree.py`\n---\n#!/usr/bin/env python
# -*- coding: utf-8 -*-
# list_tree.py

"""
A command-line utility to display the structure of a directory in a tree-like format.

Supports:
- Limiting traversal depth
- Displaying item counts
- Suppressing specific subfolders
- Listing and printing script files of a specific type
- Writing output to a file
- Quiet mode to suppress console output
"""

import argparse
from pathlib import Path
import sys
import io

TEE    = "├──"
CORNER = "└──"
PIPE   = "│   "
SPACE  = "    "

def list_tree(
    root: str | Path = ".",
    *,
    depth: int = 3,
    show_count: bool = False,
    suppress: list[str] | None = None,
    return_str: bool = False,
) -> str | None:
    """
    Thin wrapper around print_tree() that **returns** the result instead
    of printing it.  Set `return_str=True` if you want the string back.
    """
    suppress = suppress or []
    out_lines: list[str] = []

    # reuse the existing console helper but capture lines
    print_tree(
        Path(root),
        depth=0,
        max_depth=depth,
        show_count=show_count,
        suppress=suppress,
        out_lines=out_lines,
        quiet=True,          # don't write to stdout
    )

    tree_str = "\n".join(out_lines)
    if return_str:
        return tree_str
    else:
        print(tree_str)
        return None

def echo(line: str, out_lines: list[str], quiet: bool) -> None:
    """
    Append line to out_lines and print it unless quiet is True.
    """
    out_lines.append(line)
    if not quiet:
        print(line)

def print_tree(
    dir_path: Path,
    prefix: str = "",
    depth: int = 0,
    max_depth: int = 3,
    show_count: bool = False,
    suppress: list[str] = [],
    out_lines: list[str] = [],
    quiet: bool = False
):
    if depth >= max_depth:
        return

    try:
        contents = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return

    pointers = [TEE] * (len(contents) - 1) + [CORNER]

    for pointer, path in zip(pointers, contents):
        if path.is_dir() and path.name.lower() in (name.lower() for name in suppress):
            continue

        count_str = ""
        if path.is_dir() and show_count:
            try:
                item_count = len(list(path.iterdir()))
                count_str = f" ({item_count} items)"
            except PermissionError:
                count_str = " (permission denied)"

        echo(f"{prefix}{pointer} {path.name}{count_str}", out_lines, quiet)

        if path.is_dir():
            extension = PIPE if pointer == TEE else SPACE
            print_tree(
                path,
                prefix + extension,
                depth + 1,
                max_depth,
                show_count,
                suppress,
                out_lines,
                quiet
            )

def list_scripts(
    dir_path: Path,
    extensions: list[str],
    suppress: list[str],
    out_lines: list[str] = [],
    quiet: bool = False
):
    echo(f"\n📜 Listing scripts with extensions: {', '.join(extensions)}", out_lines, quiet)
    echo("-" * 40, out_lines, quiet)

    for path in dir_path.rglob("*"):
        if not path.is_file():
            continue
        if any(path.suffix.lower() == ext.lower() for ext in extensions):
            if any(part.lower() in (s.lower() for s in suppress) for part in path.parts):
                continue  # skip suppressed folders

            echo(f"\n### {path.name}\n", out_lines, quiet)
            try:
                content = path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    echo(line, out_lines, quiet)
            except Exception as e:
                echo(f"(Could not read file: {e})", out_lines, quiet)

    echo("\n" + "-" * 40, out_lines, quiet)

def main():
    parser = argparse.ArgumentParser(
        description="Display a directory structure as a tree.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        type=Path,
        help="The target directory to scan."
    )
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=3,
        help="Max depth of subfolders to display. Default is 3."
    )
    parser.add_argument(
        "-c", "--count",
        action="store_true",
        help="Show number of items inside each subdirectory."
    )
    parser.add_argument(
        "-s", "--suppress",
        nargs="*",
        default=[],
        help="List of folder names to suppress (case-insensitive)."
    )
    parser.add_argument(
        "-l", "--list-scripts",
        nargs="*",
        default=[],
        help="Extensions of script files to print, e.g. .py .ts .yaml"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write all output to a file instead of (or in addition to) printing."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output. Use with --output."
    )

    args = parser.parse_args()

    # validate directory
    if not args.directory.exists() or not args.directory.is_dir():
        print(f"Error: Invalid directory '{args.directory}'", file=sys.stderr)
        sys.exit(1)

    out_lines: list[str] = []
    quiet = bool(args.quiet)

    # header
    echo(f"\n📁 Tree for: {args.directory.resolve()}", out_lines, quiet)
    echo("-" * 40, out_lines, quiet)

    # root line
    root_count = f" ({len(list(args.directory.iterdir()))} items)" if args.count else ""
    echo(f"{args.directory.name}{root_count}", out_lines, quiet)

    # tree
    print_tree(
        args.directory,
        depth=0,
        max_depth=args.depth,
        show_count=args.count,
        suppress=args.suppress,
        out_lines=out_lines,
        quiet=quiet
    )

    # scripts
    if args.list_scripts:
        list_scripts(
            args.directory,
            extensions=args.list_scripts,
            suppress=args.suppress,
            out_lines=out_lines,
            quiet=quiet
        )

    echo("-" * 40, out_lines, quiet)

    # write to file if requested
    if args.output:
        try:
            args.output.write_text("\n".join(out_lines), encoding="utf-8")
            if not quiet:
                print(f"\n📁 Output written to: {args.output.resolve()}")
        except Exception as e:
            print(f"❌ Failed to write output: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
\n\n### 11. `src\oneclick_context\utils.py`\n---\n﻿from pathlib import Path
from typing import Optional
import inspect, click, typer

COMMON_LIBS = ["node_modules", "dist", ".venv", ".git", "__pycache__"]

def _abort_if_none(val):
    """Exit CLI (code 0) when Questionary returns None (Esc / Ctrl-C)."""
    if val is None:
        raise typer.Exit()
    return val

def sanitize_path(raw: Optional[str]) -> Path:
    """
    Return absolute Path from user input.
    If *raw* is None/blank → current working directory.
    """
    if raw is None or not str(raw).strip():
        return Path.cwd()
    return (
        Path(str(raw).strip().lstrip("./").strip('"'))
        .expanduser()
        .resolve()
    )

def discover_extensions(root: Path, suppress: list[str]) -> list[str]:
    """
    Return a sorted list of unique file suffixes ('.py', '.ts', …)
    under *root*, skipping suppressed directories.
    """
    suppress_lc = {s.lower() for s in suppress}
    exts: set[str] = set()
    for p in root.rglob("*"):
        if not p.is_file() or not p.suffix:
            continue
        if any(part.lower() in suppress_lc for part in p.parts):
            continue
        exts.add(p.suffix)
    return sorted(exts, key=str.lower)


SUPPORTS_HYPERLINK = "hyperlink" in inspect.signature(click.style).parameters
\n\n### 12. `src\oneclick_context\__init__.py`\n---\n\n\n### 13. `src\oneclick_context\exporters\html.py`\n---\n﻿def _render_li(node):
    if node["type"] == "file":
        return f"<li>{node['name']}</li>"
    children_html = "".join(_render_li(c) for c in node["children"])
    return f"<li><details><summary>{node['name']}</summary><ul>{children_html}</ul></details></li>"

def render_html(tree_obj):
    return f"<ul>{_render_li(tree_obj)}</ul>"
\n\n### 14. `src\oneclick_context\exporters\json.py`\n---\n﻿import json
def render_json(tree_obj):
    return json.dumps(tree_obj, indent=2)
\n\n### 15. `src\oneclick_context\exporters\markdown.py`\n---\n﻿from pathlib import Path
from .text import render

def render_md(tree_obj, folder: Path):
    body = "\n".join(render(tree_obj))
    name = folder.name or str(folder)
    return (
        f"<details><summary>📁 {name}</summary>\n\n"
        "```text\n"
        f"{body}\n"
        "```\n"
        "</details>"
    )
\n\n### 16. `src\oneclick_context\exporters\text.py`\n---\n﻿TEE, CORNER, PIPE, SPACE = "├──", "└──", "│   ", "    "

def render(node, prefix=""):
    lines = []
    children = node["children"]
    pointers = [TEE] * (len(children) - 1) + [CORNER]
    for pointer, child in zip(pointers, children):
        lines.append(f"{prefix}{pointer} {child['name']}")
        if child["type"] == "dir":
            extension = PIPE if pointer == TEE else SPACE
            lines.extend(render(child, prefix + extension))
    return lines
\n\n### 17. `src\oneclick_context\exporters\__init__.py`\n---\n﻿from . import text, markdown, json, html  # noqa: F401
