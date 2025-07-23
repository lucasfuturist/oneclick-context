from subprocess import run, PIPE
from pathlib import Path

def test_json_output(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.txt").write_text("x")
    result = run(["oneclick", str(tmp_path), "--fmt", "json"], stdout=PIPE, text=True)
    assert result.returncode == 0
    assert '"a.txt"' in result.stdout
