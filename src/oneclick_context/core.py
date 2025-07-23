from pathlib import Path
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
