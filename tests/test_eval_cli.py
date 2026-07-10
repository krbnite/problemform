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
DECISIONS_SUITE = Path(__file__).parent.parent / "benchmarks" / "decisions"  # formulation-only


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
        """Fails the 2nd *comparative* judgment; answers all other lenses.

        Since α.4 also drives property checks off each case's expected_properties,
        the judge receives property verdicts interleaved with comparative ones.
        We count only comparative calls so the injected failure lands on a
        specific case's answer judgment (case #2), independent of how many
        property calls precede it.
        """

        comparative_calls = 0
        model = "claude-test"

        def generate_text(self, *a, **kw):
            return ""

        def generate_structured(self, prompt, output_model, **kw):
            fields = set(output_model.model_fields)
            if output_model is ComparativeJudgmentResult:
                _PartiallyFailingJudge.comparative_calls += 1
                if _PartiallyFailingJudge.comparative_calls == 2:
                    raise RuntimeError("intermittent judge error")
                return ComparativeJudgmentResult(
                    winner="b", materiality="material",
                    rationale="r", key_differences=[],
                )
            if "holds" in fields:
                return output_model(holds=True, rationale="r")
            if "raw_score" in fields:
                return output_model(raw_score=4, rationale="r")
            raise AssertionError(f"unexpected output_model: {output_model!r}")

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


def test_benchmark_loads_default_rubrics_and_properties(runner, monkeypatch, tmp_path: Path):
    """With no --rubric/--property-suite, the shipped defaults load and run."""
    _install_three_role_stubs(monkeypatch)
    result = runner.invoke(
        app,
        ["benchmark", str(SUITE), "--output", str(tmp_path / "run"), "--format", "json"],
    )
    assert result.exit_code == 0, result.stderr
    report = BenchmarkReport.model_validate_json((tmp_path / "run" / "report.json").read_text())
    # Both default rubrics ran.
    assert {"formulation_quality_v1", "answer_quality_v1"} <= set(report.aggregate_rubrics)
    # Default artifact suite ran, plus per-case expected_properties activation.
    assert "addresses_stated_request" in report.aggregate_properties
    assert len(report.aggregate_properties) > 4  # 4 shared + activated per-case


def test_benchmark_explicit_rubric_overrides_defaults(runner, monkeypatch, tmp_path: Path):
    """An explicit --rubric replaces the default rubric set entirely."""
    _install_three_role_stubs(monkeypatch)
    custom = tmp_path / "custom_rubric.yaml"
    custom.write_text(
        "name: custom_rubric_x\n"
        "description: test\n"
        "target: formulation\n"
        "mode: absolute\n"
        "criteria:\n"
        "  - name: c\n"
        "    description: d\n"
        "    weight: 1.0\n"
        "    scoring: graded_5\n"
    )
    result = runner.invoke(
        app,
        ["benchmark", str(SUITE), "--output", str(tmp_path / "run"),
         "--rubric", str(custom), "--format", "json"],
    )
    assert result.exit_code == 0, result.stderr
    report = BenchmarkReport.model_validate_json((tmp_path / "run" / "report.json").read_text())
    assert set(report.aggregate_rubrics) == {"custom_rubric_x"}
    assert "formulation_quality_v1" not in report.aggregate_rubrics


def test_benchmark_no_answer_comparison_builds_no_answer_provider(runner, monkeypatch, tmp_path: Path):
    """--no-answer-comparison over the (answerable) default suite must skip the answer
    lens, build no answer provider, emit no same-family warning, and record 'not_used'."""
    pf = _PFStub()
    judge = _JudgeStub()
    queue = [pf, judge]  # only pf + judge should be constructed (no answer provider)
    monkeypatch.setattr(cli_module, "make_provider", lambda *a, **kw: queue.pop(0))

    result = runner.invoke(
        app,
        ["benchmark", str(SUITE), "--no-answer-comparison",
         "--output", str(tmp_path / "run"), "--format", "json"],
    )
    assert result.exit_code == 0, result.stderr
    assert queue == []  # exactly pf + judge consumed; no third (answer) construction
    report = BenchmarkReport.model_validate_json((tmp_path / "run" / "report.json").read_text())
    assert report.aggregate.n_answer_skipped == 5
    assert report.aggregate.n_completed == 0
    assert report.config["answer_provider"] == "not_used"
    assert report.config["answer_model"] == "not_used"
    assert report.config["answer_comparison"] == "forced_off"
    combined = (result.stderr or "") + (result.output or "")
    assert "self-preference" not in combined


def test_benchmark_formulation_only_suite_skips_answer_lens_by_policy(runner, monkeypatch, tmp_path: Path):
    """A wholly formulation-only suite (decisions) skips the answer lens by default —
    no answer provider built, all cases answer-skipped, config records not_used."""
    pf = _PFStub()
    judge = _JudgeStub()
    queue = [pf, judge]  # answer provider must NOT be constructed
    monkeypatch.setattr(cli_module, "make_provider", lambda *a, **kw: queue.pop(0))

    result = runner.invoke(
        app,
        ["benchmark", str(DECISIONS_SUITE), "--output", str(tmp_path / "run"), "--format", "json"],
    )
    assert result.exit_code == 0, result.stderr
    assert queue == []  # pf + judge only
    report = BenchmarkReport.model_validate_json((tmp_path / "run" / "report.json").read_text())
    assert report.aggregate.n_answer_skipped == 2
    assert report.aggregate.n_completed == 0
    assert report.config["answer_provider"] == "not_used"
    assert report.config["answer_comparison"] == "per_type_policy"


def test_benchmark_force_answer_comparison_on_formulation_only_suite(runner, monkeypatch, tmp_path: Path):
    """--answer-comparison forces the lens on for formulation-only types: the answer
    provider is built and both decision cases complete."""
    _install_three_role_stubs(monkeypatch)  # pf, answer, judge all consumed
    result = runner.invoke(
        app,
        ["benchmark", str(DECISIONS_SUITE), "--answer-comparison",
         "--output", str(tmp_path / "run"), "--format", "json"],
    )
    assert result.exit_code == 0, result.stderr
    report = BenchmarkReport.model_validate_json((tmp_path / "run" / "report.json").read_text())
    assert report.aggregate.n_completed == 2
    assert report.aggregate.n_answer_skipped == 0
    assert report.config["answer_comparison"] == "forced_on"
    assert report.config["answer_provider"] != "not_used"
