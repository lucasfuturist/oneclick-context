#!/usr/bin/env python
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
