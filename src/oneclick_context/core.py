"""
Core helpers – build_tree()

Now supports:
• max_depth   – unchanged
• suppress    – skip folders by name (case-insensitive)
• extra_exts  – only include files whose suffix is in this allow-list
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict, List, Optional, Set


class Node(TypedDict):
    type: str         # "file" | "dir"
    name: str
    children: List["Node"]


def build_tree(
    root: Path,
    *,
    max_depth: int = 3,
    suppress: Optional[List[str]] = None,
    extra_exts: Optional[List[str]] = None,
    _depth: int = 0,
) -> Node:
    """Return a nested dict representing *root*’s directory tree."""

    suppress_set: Set[str] = {s.lower() for s in (suppress or [])}
    ext_filter: Optional[Set[str]] = (
        {e if e.startswith(".") else f".{e}" for e in extra_exts} if extra_exts else None
    )

    node: Node = {"type": "dir", "name": root.name, "children": []}

    if _depth >= max_depth:
        return node

    try:
        # dirs first, then files; both alphabetically case-insensitive
        entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:  # unreadable dir – skip silently
        return node

    for entry in entries:
        if entry.is_dir():
            if entry.name.lower() in suppress_set:
                continue
            node["children"].append(
                build_tree(
                    entry,
                    max_depth=max_depth,
                    suppress=suppress,
                    extra_exts=extra_exts,
                    _depth=_depth + 1,
                )
            )
        elif entry.is_file():
            if ext_filter and entry.suffix not in ext_filter:
                continue
            node["children"].append(
                {"type": "file", "name": entry.name, "children": []}
            )

    return node
