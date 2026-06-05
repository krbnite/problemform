import pytest

from problemform.eval.models import PropertyCheck, PropertyCheckResult
from problemform.eval.property_runner import (
    _PropertyVerdict,
    run_property_check,
    run_property_checks,
)


class _RecordingPropertyJudge:
    """Stub LLMProvider that records prompts and returns scripted verdicts.

    ``verdicts`` is an iterable of (holds, rationale) pairs consumed in order.
    """

    model = "stub-property-judge"

    def __init__(self, verdicts):
        self._verdicts = iter(verdicts)
        self.prompts: list[str] = []

    def generate_text(self, *a, **kw):
        raise AssertionError("property runner should not call generate_text")

    def generate_structured(self, prompt, output_model, **kw):
        assert output_model is _PropertyVerdict
        self.prompts.append(prompt)
        holds, rationale = next(self._verdicts)
        return _PropertyVerdict(holds=holds, rationale=rationale)


def _property(name: str, target: str = "artifact", expected: bool = True) -> PropertyCheck:
    return PropertyCheck(
        name=name, description=f"check {name}", target=target,  # type: ignore[arg-type]
        expected=expected,
    )


def test_run_property_check_passes_when_holds_matches_expected_true():
    p = _property("x", expected=True)
    judge = _RecordingPropertyJudge([(True, "matches")])

    result = run_property_check(p, "subject", "refined", judge)

    assert isinstance(result, PropertyCheckResult)
    assert result.property_name == "x"
    assert result.target == "artifact"
    assert result.subject == "refined"
    assert result.holds is True
    assert result.expected is True
    assert result.passed is True
    assert result.rationale == "matches"


def test_run_property_check_passes_when_holds_matches_expected_false():
    """``expected=False`` asserts the property should NOT hold; the judge
    confirming holds=False is a *pass*, not a failure."""
    p = _property("no_pii_leak", expected=False)
    judge = _RecordingPropertyJudge([(False, "no PII observed")])

    result = run_property_check(p, "subject", "refined", judge)

    assert result.holds is False
    assert result.expected is False
    assert result.passed is True


def test_run_property_check_fails_when_holds_diverges_from_expected():
    """holds=True with expected=False is a *fail*; vice versa for True/False."""
    p_true = _property("addresses_request", expected=True)
    judge_true = _RecordingPropertyJudge([(False, "off-topic")])
    result_true = run_property_check(p_true, "subj", "raw", judge_true)
    assert result_true.passed is False
    assert result_true.holds is False
    assert result_true.expected is True

    p_false = _property("no_pii_leak", expected=False)
    judge_false = _RecordingPropertyJudge([(True, "leaked an email")])
    result_false = run_property_check(p_false, "subj", "raw", judge_false)
    assert result_false.passed is False
    assert result_false.holds is True
    assert result_false.expected is False


def test_run_property_check_uses_target_aware_prompt():
    p_formulation = _property("clear_claim", target="formulation")
    judge = _RecordingPropertyJudge([(True, "yes")])
    run_property_check(p_formulation, "subject", "refined", judge)
    assert "Formulation:" in judge.prompts[0]
    assert "Artifact:" not in judge.prompts[0]

    p_artifact = _property("respectful", target="artifact")
    judge2 = _RecordingPropertyJudge([(True, "yes")])
    run_property_check(p_artifact, "subject", "refined", judge2)
    assert "Artifact:" in judge2.prompts[0]
    assert "Formulation:" not in judge2.prompts[0]


def test_run_property_checks_preserves_input_order():
    props = [
        _property("p_a", expected=True),
        _property("p_b", expected=False),
        _property("p_c", expected=True),
    ]
    judge = _RecordingPropertyJudge([
        (True,  "a holds"),
        (False, "b does not hold (as expected)"),
        (True,  "c holds"),
    ])

    results = run_property_checks(props, "subject", "raw", judge)

    assert [r.property_name for r in results] == ["p_a", "p_b", "p_c"]
    assert all(r.passed for r in results)
    assert all(r.subject == "raw" for r in results)
