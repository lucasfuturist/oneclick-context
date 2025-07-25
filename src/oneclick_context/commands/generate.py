"""
Generate a directory tree and send it to stdout or a file.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple, List  # <-- Correctly import List
from rich.console import Console
from ..core import build_tree
from ..exporters import text, markdown, json as jsonexp, html

FMT_MAP = {
    "text": lambda t, p: "\n".join(text.render(t)),
    "md": markdown.render_md,
    "json": lambda t, p: jsonexp.render_json(t),
    "html": lambda t, p: html.render_html(t),
}

console = Console()

def _get_script_contents(root: Path, inline_exts: Tuple[str, ...]) -> str:
    """Finds, reads, and formats the content of specified script files."""
    output: List[str] = []
    
    extensions = {f".{ext.lstrip('.')}" for ext in inline_exts}
    
    files_to_inline = [p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix in extensions]

    if not files_to_inline:
        return ""

    output.append(f"\n\n--- 📜 Scripts Content ({', '.join(inline_exts)}) ---\n")

    for file_path in files_to_inline:
        relative_path = file_path.relative_to(root)
        output.append(f"\n### 📄 {relative_path}\n")
        try:
            content = file_path.read_text(encoding="utf-8")
            output.append("```")
            output.append(content)
            output.append("```")
        except Exception as e:
            output.append(f"Could not read file: {e}")
    
    return "\n".join(output)

def generate_output(
    root: Path,
    depth: int,
    fmt: str,
    output_path: Optional[Path] = None,
    languages: Tuple[str, ...] = (),
    inline_exts: Tuple[str, ...] = (),
) -> None:
    """Build the tree, optionally inline scripts, and render it."""
    tree = build_tree(root=root, max_depth=depth, extra_exts=list(languages))
    rendered = FMT_MAP[fmt.lower()](tree, root)

    if inline_exts and fmt.lower() in ("text", "md"):
        script_content = _get_script_contents(root, inline_exts)
        rendered += script_content

    if output_path:
        dst = output_path.expanduser().resolve()
        dst.write_text(rendered, encoding="utf-8")
        console.print(f"[green]✓ Saved to [link={dst.as_uri()}]{dst}[/link][/green]")
    else:
        console.print(rendered)
