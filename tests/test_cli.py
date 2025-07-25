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

def test_language_filter(tmp_path: Path):
    """Verify that the --lang flag correctly filters files by extension."""
    # Create a test structure with different file types
    (tmp_path / "a.py").write_text("python")
    (tmp_path / "b.js").write_text("javascript")
    (tmp_path / "c.toml").write_text("toml")

    # Run the command with filters for .py and .toml
    result = runner.invoke(app, [
        "--path", str(tmp_path),
        "--lang", ".py",
        "--lang", ".toml"
    ])

    # Assert the command ran successfully
    assert result.exit_code == 0
    assert result.exception is None

    # Assert that the output contains the desired files
    assert "a.py" in result.stdout
    assert "c.toml" in result.stdout

    # Assert that the filtered-out file is NOT in the output
    assert "b.js" not in result.stdout

def test_markdown_output(tmp_path: Path):
    """Verify that the --format md flag produces a collapsible Markdown block."""
    # Create a dummy file in the temp directory
    (tmp_path / "file.txt").write_text("content")

    # Run the command to generate Markdown output
    result = runner.invoke(app, [
        "--path", str(tmp_path),
        "--format", "md"
    ])

    # Assert the command ran successfully
    assert result.exit_code == 0
    assert result.exception is None

    # Assert that the output contains the key elements of our Markdown format
    assert "<details><summary>" in result.stdout
    assert "```text" in result.stdout
    assert "file.txt" in result.stdout
    assert "```" in result.stdout
    assert "</details>" in result.stdout

def test_html_output(tmp_path: Path):
    """Verify that the --format html flag produces a collapsible HTML list."""
    # Create a dummy file in the temp directory
    (tmp_path / "file.txt").write_text("content")

    # Run the command to generate HTML output
    result = runner.invoke(app, [
        "--path", str(tmp_path),
        "--format", "html"
    ])

    # Assert the command ran successfully
    assert result.exit_code == 0
    assert result.exception is None

    # Assert that the output contains key HTML tags for a nested list
    assert "<ul>" in result.stdout
    assert "<li>" in result.stdout
    assert "<details><summary>" in result.stdout
    assert "file.txt" in result.stdout
    assert "</details>" in result.stdout
    assert "</ul>" in result.stdout
