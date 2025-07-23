from pathlib import Path
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
