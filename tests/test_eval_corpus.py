from pathlib import Path

import pytest

from problemform.eval.corpus import (
    CorpusError,
    load_property_suite,
    load_rubrics,
    load_test_cases,
)

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


# --- M3B-α: rubric loader --------------------------------------------------


def _rubric_yaml(name: str = "demo_rubric") -> str:
    return (
        f"name: {name}\n"
        "description: a demo rubric for tests\n"
        "target: formulation\n"
        "mode: absolute\n"
        "criteria:\n"
        "  - name: central_claim\n"
        "    description: names a central claim\n"
        "  - name: assumption_surfacing\n"
        "    description: surfaces load-bearing assumptions\n"
        "    weight: 2.0\n"
        "    scoring: graded_3\n"
    )


def test_load_rubrics_from_single_file(tmp_path: Path):
    f = tmp_path / "one.yaml"
    f.write_text(_rubric_yaml())
    rubrics = load_rubrics(f)
    assert len(rubrics) == 1
    r = rubrics[0]
    assert r.name == "demo_rubric"
    assert r.target == "formulation"
    assert r.mode == "absolute"
    assert len(r.criteria) == 2
    assert r.criteria[1].weight == 2.0
    assert r.criteria[1].scoring == "graded_3"


def test_load_rubrics_from_directory_walks_recursively(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.yaml").write_text(_rubric_yaml("rubric_a"))
    (tmp_path / "b.yml").write_text(_rubric_yaml("rubric_b"))
    rubrics = load_rubrics(tmp_path)
    assert {r.name for r in rubrics} == {"rubric_a", "rubric_b"}


def test_load_rubrics_rejects_non_yaml_file(tmp_path: Path):
    f = tmp_path / "not_yaml.txt"
    f.write_text(_rubric_yaml())
    with pytest.raises(CorpusError, match="\\.yaml/\\.yml"):
        load_rubrics(f)


def test_load_rubrics_rejects_missing_path(tmp_path: Path):
    with pytest.raises(CorpusError, match="does not exist"):
        load_rubrics(tmp_path / "nope.yaml")


def test_load_rubrics_rejects_malformed_yaml(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not a mapping")
    with pytest.raises(CorpusError, match="top-level must be a mapping"):
        load_rubrics(bad)


def test_load_rubrics_rejects_missing_required_field(tmp_path: Path):
    incomplete = tmp_path / "incomplete.yaml"
    incomplete.write_text(
        "name: x\n"
        "description: y\n"
        "target: formulation\n"
        "mode: absolute\n"
        # no criteria
    )
    with pytest.raises(CorpusError):
        load_rubrics(incomplete)


# --- M3B-α: property-suite loader ------------------------------------------


def _property_suite_yaml_with_key() -> str:
    return (
        "suite_name: demo_suite\n"
        "properties:\n"
        "  - name: addresses_audience\n"
        "    description: answer addresses the intended audience\n"
        "    target: artifact\n"
        "  - name: factually_accurate\n"
        "    description: answer is factually accurate\n"
        "    target: artifact\n"
    )


def _property_list_yaml() -> str:
    return (
        "- name: surfaces_central_claim\n"
        "  description: formulation names a central claim\n"
        "  target: formulation\n"
        "- name: no_assumption_buried\n"
        "  description: formulation does not bury its key assumption\n"
        "  target: formulation\n"
        "  expected: false\n"
    )


def test_load_property_suite_from_keyed_file(tmp_path: Path):
    f = tmp_path / "suite.yaml"
    f.write_text(_property_suite_yaml_with_key())
    props = load_property_suite(f)
    assert len(props) == 2
    assert props[0].name == "addresses_audience"
    assert props[0].target == "artifact"
    assert props[1].expected is True


def test_load_property_suite_from_bare_list_file(tmp_path: Path):
    f = tmp_path / "list.yaml"
    f.write_text(_property_list_yaml())
    props = load_property_suite(f)
    assert {p.name for p in props} == {
        "surfaces_central_claim",
        "no_assumption_buried",
    }
    no_buried = next(p for p in props if p.name == "no_assumption_buried")
    assert no_buried.expected is False


def test_load_property_suite_from_directory_walks_recursively(tmp_path: Path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.yaml").write_text(_property_suite_yaml_with_key())
    (tmp_path / "b.yml").write_text(_property_list_yaml())
    props = load_property_suite(tmp_path)
    assert len(props) == 4
    assert {p.name for p in props} == {
        "addresses_audience",
        "factually_accurate",
        "surfaces_central_claim",
        "no_assumption_buried",
    }


def test_load_property_suite_rejects_scalar_top_level(tmp_path: Path):
    f = tmp_path / "scalar.yaml"
    f.write_text("just a string")
    with pytest.raises(CorpusError, match="must be either a list of"):
        load_property_suite(f)


def test_load_property_suite_rejects_non_list_properties_value(tmp_path: Path):
    f = tmp_path / "bad_shape.yaml"
    f.write_text("properties:\n  not_a_list: true\n")
    with pytest.raises(CorpusError, match="'properties' must be a list"):
        load_property_suite(f)


def test_load_property_suite_rejects_non_mapping_entry(tmp_path: Path):
    f = tmp_path / "bad_entry.yaml"
    f.write_text("properties:\n  - just_a_string\n")
    with pytest.raises(CorpusError, match="must be a mapping"):
        load_property_suite(f)


def test_load_property_suite_rejects_missing_required_field(tmp_path: Path):
    f = tmp_path / "missing_target.yaml"
    f.write_text(
        "properties:\n"
        "  - name: x\n"
        "    description: y\n"
        # no target
    )
    with pytest.raises(CorpusError):
        load_property_suite(f)


# --- M3B-α.2: default rubrics and shared property suite parse-tests ---------


DEFAULT_RUBRICS = Path(__file__).parent.parent / "benchmarks" / "rubrics"
DEFAULT_PROPERTIES = Path(__file__).parent.parent / "benchmarks" / "properties"


def test_default_rubrics_parse_from_directory():
    rubrics = load_rubrics(DEFAULT_RUBRICS)
    by_name = {r.name: r for r in rubrics}
    assert "formulation_quality_v1" in by_name
    assert "answer_quality_v1" in by_name

    fq = by_name["formulation_quality_v1"]
    aq = by_name["answer_quality_v1"]
    assert fq.target == "formulation"
    assert fq.mode == "absolute"
    assert aq.target == "artifact"
    assert aq.mode == "absolute"

    # α.2 ships five criteria per default rubric, all graded_5 / weight 1.0.
    for r in (fq, aq):
        assert len(r.criteria) == 5
        for c in r.criteria:
            assert c.scoring == "graded_5"
            assert c.weight == 1.0


def test_default_rubrics_parse_from_file_paths():
    fq = load_rubrics(DEFAULT_RUBRICS / "formulation_quality_v1.yaml")
    aq = load_rubrics(DEFAULT_RUBRICS / "answer_quality_v1.yaml")
    assert len(fq) == 1 and fq[0].name == "formulation_quality_v1"
    assert len(aq) == 1 and aq[0].name == "answer_quality_v1"


def test_default_formulation_rubric_uses_canonical_criteria():
    [fq] = load_rubrics(DEFAULT_RUBRICS / "formulation_quality_v1.yaml")
    assert [c.name for c in fq.criteria] == [
        "central_claim_clarity",
        "assumption_surfacing",
        "constraint_articulation",
        "alternative_framing_coverage",
        "meta_question_presence",
    ]


def test_default_answer_rubric_uses_expected_criteria():
    [aq] = load_rubrics(DEFAULT_RUBRICS / "answer_quality_v1.yaml")
    assert [c.name for c in aq.criteria] == [
        "directness",
        "factual_care",
        "reasoning_quality",
        "constraint_satisfaction",
        "usefulness",
    ]


def test_default_property_suite_parses_from_directory():
    props = load_property_suite(DEFAULT_PROPERTIES)
    names = {p.name for p in props}
    assert {
        "addresses_stated_request",
        "no_unnecessary_refusal",
        "no_obvious_unsupported_facts",
        "respectful_tone",
    } <= names
    for p in props:
        assert p.target == "artifact"
        assert p.expected is True


def test_default_property_suite_parses_from_file_path():
    props = load_property_suite(DEFAULT_PROPERTIES / "artifact_baseline_v1.yaml")
    assert len(props) == 4
    for p in props:
        assert p.target == "artifact"
        assert p.expected is True
