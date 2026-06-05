from pathlib import Path

import pytest
from typer.testing import CliRunner

from problemform import cli as cli_module
from problemform.cli import app
from problemform.eval.judges import ComparativeJudgmentResult
from problemform.eval.models import BenchmarkReport
from tests.test_eval_engine import _AnswerStub, _JudgeStub, _PFStub  # reuse


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


SUITE = Path(__file__).parent.parent / "benchmarks" / "default"


def _install_three_role_stubs(monkeypatch):
    """Return distinct stubs per role; monkey-patch cli_module.make_provider."""
    pf = _PFStub()
    answer = _AnswerStub()
    judge = _JudgeStub(winner="b", materiality="material")

    # cli_module.make_provider is called three times in the benchmark command,
    # in the order: pf, answer, judge. Return them in that order.
    queue = [pf, answer, judge]

    def fake_make_provider(*a, **kw):
        return queue.pop(0)

    monkeypatch.setattr(cli_module, "make_provider", fake_make_provider)
    return pf, answer, judge


def test_benchmark_runs_starter_suite_and_writes_reports(runner, monkeypatch, tmp_path: Path):
    _install_three_role_stubs(monkeypatch)
    result = runner.invoke(
        app,
        ["benchmark", str(SUITE), "--output", str(tmp_path / "run"), "--format", "json"],
    )
    assert result.exit_code == 0, result.stderr
    run_dir = tmp_path / "run"
    assert (run_dir / "report.json").exists()
    assert (run_dir / "report.md").exists()
    report = BenchmarkReport.model_validate_json((run_dir / "report.json").read_text())
    # All 5 starter cases were attempted.
    assert report.aggregate.n_cases == 5


def test_benchmark_warns_on_same_family_judge(runner, monkeypatch, tmp_path: Path):
    """Same-provider answer+judge must warn loudly but not block."""
    pf = _PFStub()
    answer = _AnswerStub()
    judge = _JudgeStub(winner="a", materiality="minor")
    # Give answer and judge the same provider class name to trigger the warning.
    answer.__class__.__name__ = "OpenAIProvider"  # type: ignore[attr-defined]
    judge.__class__.__name__ = "OpenAIProvider"   # type: ignore[attr-defined]
    answer.model = "gpt-5.4"                       # type: ignore[attr-defined]
    judge.model = "gpt-5.4"                        # type: ignore[attr-defined]
    pf.model = "gpt-5.4"                           # type: ignore[attr-defined]

    queue = [pf, answer, judge]
    monkeypatch.setattr(cli_module, "make_provider", lambda *a, **kw: queue.pop(0))

    result = runner.invoke(
        app,
        ["benchmark", str(SUITE), "--output", str(tmp_path / "run"), "--format", "json"],
    )
    assert result.exit_code == 0, result.stderr
    combined = (result.stderr or "") + (result.output or "")
    assert "warning" in combined.lower()
    assert "self-preference" in combined

    report = BenchmarkReport.model_validate_json((tmp_path / "run" / "report.json").read_text())
    assert any("self-preference" in w for w in report.bias_warnings)


def test_benchmark_continues_on_judge_failure(runner, monkeypatch, tmp_path: Path):
    """A single failing judge call must not abort the run."""
    pf = _PFStub()
    answer = _AnswerStub()

    class _PartiallyFailingJudge:
        calls = 0
        model = "claude-test"

        def generate_text(self, *a, **kw):
            return ""

        def generate_structured(self, prompt, output_model, **kw):
            _PartiallyFailingJudge.calls += 1
            if _PartiallyFailingJudge.calls == 2:
                raise RuntimeError("intermittent judge error")
            return ComparativeJudgmentResult(
                winner="b", materiality="material",
                rationale="r", key_differences=[],
            )

    queue = [pf, answer, _PartiallyFailingJudge()]
    monkeypatch.setattr(cli_module, "make_provider", lambda *a, **kw: queue.pop(0))

    result = runner.invoke(
        app,
        ["benchmark", str(SUITE), "--output", str(tmp_path / "run"), "--format", "json"],
    )
    assert result.exit_code == 0, result.stderr
    report = BenchmarkReport.model_validate_json((tmp_path / "run" / "report.json").read_text())
    assert report.aggregate.n_cases == 5
    assert report.aggregate.n_errored == 1
    assert report.aggregate.n_completed == 4
