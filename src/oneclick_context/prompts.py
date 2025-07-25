# Standard library imports
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports
import questionary as q
try:
    from questionary import QuestionaryError
except ImportError:
    class QuestionaryError(Exception): pass

# First-party imports
from .commands.generate import generate_output
from .utils import discover_extensions, sanitize_path

# --- Constants ---
COMMON_LIBS = ["node_modules", "dist", ".venv", ".git", "__pycache__"]
SAVE_DIR_ENV_VAR = "ONECLICK_SAVE_DIR"
CONFIG_FILE = Path.home() / ".oneclick_rc.json"
SEPARATOR = ("-" * 20, "fg:#888888")

# --- Internal Helpers ---
def _abort_if_none(val):
    if val is None: raise QuestionaryError("User cancelled.")
    return val

def _ask_tree_params(root_path: Path, defaults: Dict[str, Any]) -> Dict[str, Any]:
    while True:
        depth_str = _abort_if_none(q.text("📏 Max recursion depth:", default=str(defaults.get("depth", 3))).ask())
        try:
            depth = int(depth_str)
            if depth > 0: break
            q.print("Please enter a positive number.", style="bold yellow")
        except (ValueError, AssertionError):
            q.print("Please enter a valid integer.", style="bold yellow")
    languages: List[str] = []
    if _abort_if_none(q.confirm("🔍 Filter by specific file types?", default=False).ask()):
        all_exts = discover_extensions(root_path, suppress=COMMON_LIBS)
        if all_exts:
            languages = _abort_if_none(q.checkbox("   Select extensions:", choices=sorted(all_exts)).ask())
    fmt = _abort_if_none(q.select("🎨 Output format:", choices=["text", "md", "json", "html"], default=defaults.get("fmt", "text")).ask())
    return {"depth": depth, "languages": tuple(languages), "fmt": fmt}

def _load_config() -> Optional[Path]:
    """Load the save directory from environment or config file."""
    # 1. Check environment variable (highest priority)
    env_path_str = os.getenv(SAVE_DIR_ENV_VAR)
    if env_path_str:
        try:
            expanded_path = os.path.expandvars(env_path_str)
            path = sanitize_path(expanded_path)
            path.mkdir(parents=True, exist_ok=True)
            return path
        except (OSError, PermissionError) as exc:
            q.print(f"⚠️  Could not use env var {SAVE_DIR_ENV_VAR}='{env_path_str}': {exc}", style="bold yellow")
    
    # 2. If no env var, check config file
    if CONFIG_FILE.is_file():
        try:
            with CONFIG_FILE.open("r") as f:
                data = json.load(f)
                path_str = data.get("save_dir")
                if path_str:
                    path = sanitize_path(path_str)
                    path.mkdir(parents=True, exist_ok=True)
                    return path
        except (json.JSONDecodeError, OSError, PermissionError) as exc:
             q.print(f"⚠️  Could not load config file at '{CONFIG_FILE}': {exc}", style="bold yellow")
    return None

def _save_config(save_dir: Optional[Path]) -> None:
    """Save the current save directory to the config file."""
    try:
        with CONFIG_FILE.open("w") as f:
            json.dump({"save_dir": str(save_dir) if save_dir else None}, f, indent=2)
    except OSError as exc:
        q.print(f"⚠️  Could not save to config file '{CONFIG_FILE}': {exc}", style="bold yellow")


# --- Public Interface (called by cli.py) ---
def run_guide(default_root: Path, default_depth: int, default_format: str, default_output: Optional[Path]) -> None:
    try:
        path_str = _abort_if_none(q.path("📁 1. Directory to scan:", default=str(default_root)).ask())
        root_path = sanitize_path(path_str)
        params = _ask_tree_params(root_path, {"depth": default_depth, "fmt": default_format})
        output_str = _abort_if_none(q.text("💾 2. Save to file? (leave blank for console)", default=str(default_output or "")).ask())
        output_path = sanitize_path(output_str) if output_str.strip() else None
        q.print("\n⏳ Generating your tree...", style="bold")
        generate_output(root=root_path, output_path=output_path, **params)
        if not output_path:
            q.print("\n✨ Done!", style="bold green")
        q.print(SEPARATOR[0], style=SEPARATOR[1])
    except (QuestionaryError, KeyboardInterrupt):
        q.print("\nOperation cancelled.", style="bold red")
        sys.exit(0)
    except Exception as e:
        q.print(f"\nAn unexpected error occurred: {e}", style="bold red")
        sys.exit(1)

def run_menu(*args, **kwargs) -> None:
    save_dir = _load_config()
    try:
        q.print("Welcome to One-Click Context Menu Mode!", style="bold italic")
        if save_dir:
            q.print(f"Loaded save directory: {save_dir}", style="fg:#888888")

        while True:
            action = _abort_if_none(q.select(
                "📂 Main Menu:",
                choices=[
                    q.Choice("🌳 Generate New Tree", value="generate"),
                    q.Choice(f"💾 Set/Change Save Directory (persists)", value="config"),
                    q.Separator(),
                    q.Choice("Exit", value="exit")
                ], use_indicator=True).ask())

            if action == "exit": break

            elif action == "config":
                path_str = _abort_if_none(q.path("Enter directory to save files in (leave blank to clear):", default=str(save_dir or "")).ask())
                new_save_dir = None
                if path_str.strip():
                    try:
                        new_save_dir = sanitize_path(path_str)
                        new_save_dir.mkdir(parents=True, exist_ok=True)
                        q.print(f"✅ Save directory set to: {new_save_dir}", style="bold green")
                    except (OSError, PermissionError) as exc:
                        new_save_dir = None
                        q.print(f"❌ Cannot use that directory: {exc}", style="bold red")
                else:
                    q.print("✅ Save directory cleared.", style="bold green")

                save_dir = new_save_dir
                _save_config(save_dir)

            elif action == "generate":
                path_str = _abort_if_none(q.path("📁 Directory to scan:", default=".").ask())
                root_path = sanitize_path(path_str)
                params = _ask_tree_params(root_path, {})
                
                output_path = None
                if save_dir:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    ext = "txt" if params["fmt"] == "text" else params["fmt"]
                    output_path = save_dir / f"tree_{ts}.{ext}"
                
                q.print("\n⏳ Generating your tree...", style="bold")
                generate_output(root=root_path, output_path=output_path, **params)
                
                if not output_path:
                    q.print("\n✨ Done!", style="bold green")
                q.print(SEPARATOR[0], style=SEPARATOR[1])
    
    except (QuestionaryError, KeyboardInterrupt):
        q.print("\n\nGoodbye!", style="bold")
        sys.exit(0)
    except Exception as e:
        q.print(f"\nAn unexpected error occurred: {e}", style="bold red")
        sys.exit(1)
