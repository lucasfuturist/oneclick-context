"""
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
