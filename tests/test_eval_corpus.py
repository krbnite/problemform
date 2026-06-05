from pathlib import Path

import pytest

from problemform.eval.corpus import CorpusError, load_test_cases

DEFAULT_SUITE = Path(__file__).parent.parent / "benchmarks" / "default"


def test_starter_corpus_loads_all_five_cases():
    cases = load_test_cases(DEFAULT_SUITE)
    assert len(cases) == 5
    names = {c.name for c in cases}
    assert names == {
        "cosmology_nothingness",
        "code_review_prep",
        "api_design_rest_vs_graphql",
        "teach_kid_to_swim",
        "what_causes_eclipses",
    }


def test_starter_corpus_includes_control_case():
    cases = load_test_cases(DEFAULT_SUITE)
    by_name = {c.name: c for c in cases}
    control = by_name["what_causes_eclipses"]
    assert control.category == "control"
    assert "control" in control.tags
    # Control's expected_properties guard against refinement bloat, not against
    # too-little clarification — matches the design intent.
    assert any("does not bloat" in p.lower() for p in control.expected_properties)


def test_missing_suite_directory_raises(tmp_path: Path):
    with pytest.raises(CorpusError, match="does not exist"):
        load_test_cases(tmp_path / "nope")


def test_path_must_be_directory(tmp_path: Path):
    f = tmp_path / "not-a-dir.yaml"
    f.write_text("name: x\ncategory: y\nraw_question: z\n")
    with pytest.raises(CorpusError, match="not a directory"):
        load_test_cases(f)


def test_malformed_yaml_raises_corpus_error(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not a mapping just a string")
    with pytest.raises(CorpusError, match="top-level must be a mapping"):
        load_test_cases(tmp_path)


def test_missing_required_field_raises(tmp_path: Path):
    incomplete = tmp_path / "incomplete.yaml"
    incomplete.write_text("name: x\ncategory: y\n")  # no raw_question
    with pytest.raises(CorpusError):
        load_test_cases(tmp_path)


def test_load_test_cases_walks_recursively(tmp_path: Path):
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "a.yaml").write_text(
        "name: a\ncategory: c\nraw_question: q\n"
    )
    (tmp_path / "b.yml").write_text(
        "name: b\ncategory: c\nraw_question: q\n"
    )
    cases = load_test_cases(tmp_path)
    assert {c.name for c in cases} == {"a", "b"}
