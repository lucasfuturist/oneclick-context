# tests/test_cli.py
from subprocess import run, PIPE
from pathlib import Path

def test_oneclick_returns_tree(tmp_path: Path):
    # Create a tiny fake project dir
    (tmp_path / "foo").mkdir()
    (tmp_path / "foo" / "bar.py").write_text("# sample")

    # Invoke CLI
    result = run(
        ["oneclick", str(tmp_path), "--depth", "2"],
        stdout=PIPE,
        text=True,
    )

    assert result.returncode == 0
    assert "bar.py" in result.stdout
