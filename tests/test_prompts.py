# tests/test_prompts.py
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import questionary as q

# Correctly import the specific exception class for modern versions,
# with a fallback for older ones.
try:
    from questionary import QuestionaryError
except ImportError:
    class QuestionaryError(Exception):
        pass

from oneclick_context.prompts import run_guide

# ── helpers ─────────────────────────────────────────────────────────────
class Stub:
    """Minimal object mimicking a Questionary prompt: .ask() -> value."""
    def __init__(self, value):
        self._value = value

    def ask(self):
        if self._value is None:
            raise QuestionaryError("User cancelled.")
        return self._value

def make_stub_sequence(answers):
    """Return a function that pops answers in FIFO order each call."""
    queue = list(answers)
    def _factory(*_args, **_kwargs):
        if not queue:
            raise AssertionError("Test stub queue exhausted. More prompts were called than answers provided.")
        return Stub(queue.pop(0))
    return _factory

# ── tests ───────────────────────────────────────────────────────────────
def test_run_guide_happy_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """End-to-end test of the interactive guide using Questionary stubs."""
    answers = [
        str(tmp_path), "2", True, [".py", ".md"], "md", str(tmp_path / "output.md"),
    ]

    stub_factory = make_stub_sequence(answers)
    monkeypatch.setattr("questionary.path", stub_factory)
    monkeypatch.setattr("questionary.text", stub_factory)
    monkeypatch.setattr("questionary.confirm", stub_factory)
    monkeypatch.setattr("questionary.checkbox", stub_factory)
    monkeypatch.setattr("questionary.select", stub_factory)

    # Mock the print function to prevent console errors during test runs
    monkeypatch.setattr("questionary.print", MagicMock())
    
    monkeypatch.setattr("oneclick_context.prompts.discover_extensions", lambda *args, **kwargs: [".py", ".md", ".js"])

    mock_generate = MagicMock()
    monkeypatch.setattr("oneclick_context.prompts.generate_output", mock_generate)

    run_guide(default_root=tmp_path, default_depth=3, default_format="text", default_output=None)

    mock_generate.assert_called_once()
    kwargs = mock_generate.call_args.kwargs
    assert kwargs["root"] == tmp_path
    assert kwargs["depth"] == 2
    assert kwargs["fmt"] == "md"
    assert kwargs["output_path"] == tmp_path / "output.md"
    assert kwargs["languages"] == (".py", ".md")
