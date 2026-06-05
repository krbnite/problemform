import random

import pytest

from problemform.eval.judges import (
    ComparativeJudgmentResult,
    _resolve_winner_actual,
    judge_answers,
)


class _RecordingJudge:
    def __init__(self, winner="a", materiality="material"):
        self.captured_prompt: str | None = None
        self.winner = winner
        self.materiality = materiality

    def generate_text(self, *a, **kw):
        return ""

    def generate_structured(self, prompt, output_model, **kw):
        assert output_model is ComparativeJudgmentResult
        self.captured_prompt = prompt
        return ComparativeJudgmentResult(
            winner=self.winner,
            materiality=self.materiality,
            rationale="r",
            key_differences=["d1"],
        )


@pytest.mark.parametrize(
    "judge_winner, presented_first, expected",
    [
        ("a", "raw", "raw"),
        ("b", "raw", "refined"),
        ("a", "refined", "refined"),
        ("b", "refined", "raw"),
        ("tie", "raw", "tie"),
        ("tie", "refined", "tie"),
    ],
)
def test_resolve_winner_actual(judge_winner, presented_first, expected):
    assert _resolve_winner_actual(judge_winner, presented_first) == expected


def test_judge_prompt_does_not_reveal_raw_vs_refined():
    judge = _RecordingJudge()
    # Seed RNG so we know the order chosen.
    rng = random.Random(0)
    judge_answers(judge, "q", raw_answer="RAW_TEXT", refined_answer="REFINED_TEXT", rng=rng)
    assert judge.captured_prompt is not None
    # The judge sees opaque A/B labels only. The strings "raw answer" / "refined
    # answer" / "refined prompt" must not appear in the prompt body that frames
    # the comparison (we tolerate substring matches in user content).
    body = judge.captured_prompt
    # Should not contain any explicit framing of which side is refined.
    for forbidden in [
        "raw answer", "refined answer", "raw prompt", "refined prompt",
        "ProblemForm", "original prompt", "improved prompt",
    ]:
        assert forbidden not in body, f"prompt leaked {forbidden!r}"


def test_judge_records_presented_first_actual():
    # Force refined-first by stubbing the RNG.
    class _RefinedFirst:
        def random(self):
            return 0.0  # < 0.5 → present_refined_first
    j = judge_answers(_RecordingJudge(winner="a"), "q", "RAW", "REFINED", rng=_RefinedFirst())
    assert j.presented_first_actual == "refined"
    # judge said "a" wins; refined was A, so winner_actual == "refined"
    assert j.winner_actual == "refined"


def test_judge_records_raw_first_path():
    class _RawFirst:
        def random(self):
            return 0.9  # >= 0.5 → present raw first
    j = judge_answers(_RecordingJudge(winner="a"), "q", "RAW", "REFINED", rng=_RawFirst())
    assert j.presented_first_actual == "raw"
    # judge said "a" wins; raw was A, so winner_actual == "raw"
    assert j.winner_actual == "raw"


def test_judge_returns_fully_populated_judgment():
    j = judge_answers(_RecordingJudge(), "q", "RAW", "REFINED")
    assert j.target == "answer"
    assert j.materiality == "material"
    assert j.rationale == "r"
    assert j.key_differences == ["d1"]
