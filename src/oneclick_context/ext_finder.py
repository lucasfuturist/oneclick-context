from pathlib import Path
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
