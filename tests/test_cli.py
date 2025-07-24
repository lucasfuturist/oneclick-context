from pathlib import Path
from typer.testing import CliRunner

from oneclick_context.cli import app

runner = CliRunner()

def test_json_output(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.txt").write_text("x")
    
    # The test now correctly calls the named --path option.
    result = runner.invoke(
        app, ["--path", str(tmp_path), "--fmt", "json"]
    )
    
    assert result.exit_code == 0, f"CLI exited with an error:\n{result.stdout}\n{result.stderr}"
    assert result.exception is None
    assert '"a.txt"' in result.stdout
