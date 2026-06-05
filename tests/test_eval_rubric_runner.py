import pytest

from problemform.eval.models import (
    AbsoluteRubricEvaluation,
    CriterionScoring,
    Rubric,
    RubricCriterion,
)
from problemform.eval.rubric_runner import _RubricCriterionVerdict, run_rubric


class _RecordingRubricJudge:
    """Stub LLMProvider that records each prompt and returns a scripted verdict.

    Pass ``scores`` as an iterable of (raw_score, rationale) pairs; one is
    consumed per ``generate_structured`` call in order.
    """

    model = "stub-rubric-judge"

    def __init__(self, scores):
        self._scores = iter(scores)
        self.prompts: list[str] = []

    def generate_text(self, *a, **kw):
        raise AssertionError("rubric runner should not call generate_text")

    def generate_structured(self, prompt, output_model, **kw):
        assert output_model is _RubricCriterionVerdict
        self.prompts.append(prompt)
        raw_score, rationale = next(self._scores)
        return _RubricCriterionVerdict(raw_score=raw_score, rationale=rationale)


def _rubric(
    criteria: list[RubricCriterion],
    target: str = "formulation",
    mode: str = "absolute",
    name: str = "demo",
) -> Rubric:
    return Rubric(
        name=name,
        description="demo rubric",
        target=target,  # type: ignore[arg-type]
        mode=mode,      # type: ignore[arg-type]
        criteria=criteria,
    )


def _crit(
    name: str,
    weight: float = 1.0,
    scoring: CriterionScoring = "graded_5",
) -> RubricCriterion:
    return RubricCriterion(
        name=name, description=f"score {name}", weight=weight, scoring=scoring,
    )


def test_run_rubric_iterates_criteria_in_order_and_records_results():
    rubric = _rubric([_crit("a"), _crit("b"), _crit("c")])
    judge = _RecordingRubricJudge([(4, "ra"), (2, "rb"), (0, "rc")])

    out = run_rubric(rubric, "the subject", "refined", judge)

    assert isinstance(out, AbsoluteRubricEvaluation)
    assert out.rubric_name == "demo"
    assert out.target == "formulation"
    assert out.subject == "refined"
    assert [cs.criterion_name for cs in out.criterion_scores] == ["a", "b", "c"]
    # graded_5: 4/4=1.0, 2/4=0.5, 0/4=0.0
    assert [cs.score for cs in out.criterion_scores] == [1.0, 0.5, 0.0]
    # raw_score preserved for debugging.
    assert [cs.raw_score for cs in out.criterion_scores] == [4, 2, 0]
    assert out.aggregate_score == pytest.approx(0.5)


def test_run_rubric_uses_weighted_average_for_aggregate():
    rubric = _rubric([_crit("a", weight=3.0), _crit("b", weight=1.0)])
    judge = _RecordingRubricJudge([(4, "r"), (0, "r")])  # 1.0 and 0.0

    out = run_rubric(rubric, "subj", "raw", judge)

    # (1.0 * 3 + 0.0 * 1) / 4 = 0.75
    assert out.aggregate_score == pytest.approx(0.75)


def test_run_rubric_handles_mixed_scoring_scales():
    rubric = _rubric([
        _crit("bin", scoring="binary"),
        _crit("g3", scoring="graded_3"),
        _crit("g5", scoring="graded_5"),
    ])
    judge = _RecordingRubricJudge([(1, "r"), (1, "r"), (2, "r")])  # 1.0, 0.5, 0.5

    out = run_rubric(rubric, "subj", "refined", judge)

    assert [cs.score for cs in out.criterion_scores] == [1.0, 0.5, 0.5]
    # uniform weights → mean = (1.0 + 0.5 + 0.5) / 3 ≈ 0.667
    assert out.aggregate_score == pytest.approx(2.0 / 3.0)


def test_run_rubric_clamps_out_of_range_raw_scores():
    rubric = _rubric([_crit("g5", scoring="graded_5")])
    # Judge returns 7, well above the 0-4 range; runner clamps to 4 → 1.0.
    judge = _RecordingRubricJudge([(7, "wrong scale")])

    out = run_rubric(rubric, "subj", "refined", judge)

    # raw_score preserved as-returned for debugging visibility.
    assert out.criterion_scores[0].raw_score == 7
    # Normalized score is clamped.
    assert out.criterion_scores[0].score == 1.0
    assert out.aggregate_score == 1.0


def test_run_rubric_target_drives_subject_kind_in_prompt():
    judge = _RecordingRubricJudge([(2, "r")])
    formulation_rubric = _rubric([_crit("a", scoring="graded_5")], target="formulation")
    run_rubric(formulation_rubric, "subject text", "refined", judge)
    assert "formulation" in judge.prompts[0].lower()
    assert "Formulation:" in judge.prompts[0]
    # Should NOT have artifact framing.
    assert "Artifact:" not in judge.prompts[0]

    judge2 = _RecordingRubricJudge([(2, "r")])
    artifact_rubric = _rubric([_crit("a", scoring="graded_5")], target="artifact")
    run_rubric(artifact_rubric, "subject text", "refined", judge2)
    assert "Artifact:" in judge2.prompts[0]
    assert "Formulation:" not in judge2.prompts[0]


def test_run_rubric_embeds_subject_text_and_criterion_details_in_prompt():
    judge = _RecordingRubricJudge([(3, "r")])
    rubric = _rubric([
        RubricCriterion(
            name="central_claim",
            description="the formulation names a central claim",
            weight=1.0,
            scoring="graded_5",
        )
    ])
    run_rubric(rubric, "MY SUBJECT TEXT", "refined", judge)

    prompt = judge.prompts[0]
    assert "MY SUBJECT TEXT" in prompt
    assert "central_claim" in prompt
    assert "the formulation names a central claim" in prompt
    # Includes the graded_5 scale spec.
    assert "0–4" in prompt


def test_run_rubric_rejects_comparative_mode():
    rubric = _rubric([_crit("a")], mode="comparative")
    judge = _RecordingRubricJudge([])

    with pytest.raises(ValueError, match="mode='absolute'"):
        run_rubric(rubric, "subj", "refined", judge)

    # Judge must not have been called.
    assert judge.prompts == []


def test_run_rubric_zero_weight_rubric_does_not_crash():
    rubric = _rubric([_crit("a", weight=0.0), _crit("b", weight=0.0)])
    judge = _RecordingRubricJudge([(4, "r"), (4, "r")])

    out = run_rubric(rubric, "subj", "refined", judge)

    # Per-criterion scores are still computed correctly.
    assert [cs.score for cs in out.criterion_scores] == [1.0, 1.0]
    # Weighted average defaults to 0.0 when total weight is zero (per scoring helper).
    assert out.aggregate_score == 0.0
