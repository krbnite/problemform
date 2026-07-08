"""Default rubric / property-suite resolution (M3B-α.4)."""

from problemform.eval.defaults import (
    DEFAULT_PROPERTIES_DIR,
    DEFAULT_RUBRICS_DIR,
    load_default_properties,
    load_default_rubrics,
)


def test_default_dirs_resolve_to_repo_benchmarks():
    assert DEFAULT_RUBRICS_DIR.name == "rubrics"
    assert DEFAULT_RUBRICS_DIR.parent.name == "benchmarks"
    assert DEFAULT_PROPERTIES_DIR.name == "properties"
    assert DEFAULT_PROPERTIES_DIR.parent.name == "benchmarks"


def test_load_default_rubrics_returns_shipped_rubrics():
    rubrics, reason = load_default_rubrics()
    assert reason is None
    names = {r.name for r in rubrics}
    assert {"formulation_quality_v1", "answer_quality_v1"} <= names
    assert all(r.mode == "absolute" for r in rubrics)


def test_load_default_properties_returns_artifact_baseline():
    props, reason = load_default_properties()
    assert reason is None
    names = {p.name for p in props}
    assert "addresses_stated_request" in names
    assert all(p.target in ("artifact", "formulation") for p in props)
