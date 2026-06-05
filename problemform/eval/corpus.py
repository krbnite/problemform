"""YAML corpus loaders for the evaluation framework.

Three loaders:

* ``load_test_cases(path)`` — one ``TestCase`` per file under a directory.
* ``load_rubrics(path)`` — one ``Rubric`` per file; accepts a single file or a
  directory walked recursively.
* ``load_property_suite(path)`` — many ``PropertyCheck``s per file; accepts a
  single file or a directory walked recursively.

See ``docs/designs/milestone_03_evaluation_framework.md`` Section 4 for the
``TestCase`` directory convention and
``docs/designs/milestone_03b_rubrics_and_properties.md`` for the M3B-α rubric
and property-suite conventions.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from problemform.eval.models import PropertyCheck, Rubric, TestCase


class CorpusError(ValueError):
    """Raised when a YAML file cannot be loaded or validated against its target model."""


def _safe_load(path: Path):
    """Parse a YAML file; surface parse errors as ``CorpusError`` with file path."""
    try:
        return yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise CorpusError(f"failed to parse YAML at {path}: {exc}") from exc


def _yaml_files(path: Path) -> list[Path]:
    """Return sorted list of ``*.yaml`` / ``*.yml`` files under ``path`` (file or dir).

    A single file path returns ``[path]`` if it has a YAML extension. A directory
    is walked recursively. Empty directories return ``[]``; nonexistent paths
    raise ``CorpusError`` here so callers don't silently get an empty list.
    """
    if not path.exists():
        raise CorpusError(f"path does not exist: {path}")
    if path.is_file():
        if path.suffix.lower() not in {".yaml", ".yml"}:
            raise CorpusError(
                f"expected a .yaml/.yml file or a directory; got {path}"
            )
        return [path]
    if path.is_dir():
        return sorted(
            list(path.rglob("*.yaml")) + list(path.rglob("*.yml"))
        )
    raise CorpusError(f"path is neither a file nor a directory: {path}")


def load_test_cases(suite_path: Path) -> list[TestCase]:
    """Load every ``*.yaml`` / ``*.yml`` file under ``suite_path`` recursively.

    Order is sorted by path for deterministic runs. Each file must parse as a
    single YAML mapping that validates against ``TestCase``; otherwise
    ``CorpusError`` is raised with the file path and the underlying error.
    """
    suite_path = Path(suite_path)
    if not suite_path.exists():
        raise CorpusError(f"suite path does not exist: {suite_path}")
    if not suite_path.is_dir():
        raise CorpusError(f"suite path is not a directory: {suite_path}")

    yaml_files = sorted(
        list(suite_path.rglob("*.yaml")) + list(suite_path.rglob("*.yml"))
    )
    cases: list[TestCase] = []
    for path in yaml_files:
        data = _safe_load(path)
        if not isinstance(data, dict):
            raise CorpusError(
                f"{path}: top-level must be a mapping; got {type(data).__name__}"
            )
        try:
            cases.append(TestCase.model_validate(data))
        except ValueError as exc:
            raise CorpusError(f"{path}: {exc}") from exc
    return cases


def load_rubrics(path: Path) -> list[Rubric]:
    """Load one or more rubrics from a YAML file or a directory of YAML files.

    Each YAML file must be a single mapping that validates against ``Rubric``.
    Directories are walked recursively; ordering is sorted by path. Callers
    can therefore pass either ``benchmarks/rubrics/formulation_quality_v1.yaml``
    or ``benchmarks/rubrics/`` interchangeably.
    """
    path = Path(path)
    rubrics: list[Rubric] = []
    for yaml_path in _yaml_files(path):
        data = _safe_load(yaml_path)
        if not isinstance(data, dict):
            raise CorpusError(
                f"{yaml_path}: top-level must be a mapping describing one Rubric; "
                f"got {type(data).__name__}"
            )
        try:
            rubrics.append(Rubric.model_validate(data))
        except ValueError as exc:
            raise CorpusError(f"{yaml_path}: {exc}") from exc
    return rubrics


def load_property_suite(path: Path) -> list[PropertyCheck]:
    """Load property checks from a YAML file or a directory of YAML files.

    A YAML file may take either of two shapes:

    * A mapping with a ``properties`` key whose value is a list of property-check
      dicts (the "suite" form; ``suite_name`` and other top-level keys ignored).
    * A bare list of property-check dicts.

    Both forms yield a flat ``list[PropertyCheck]``; directories aggregate
    every file's properties in path-sorted order.

    Note (M3B-α.2/β design): the flat return loses suite identity (the
    originating file or top-level ``suite_name``). For M3B-α this is
    intentional — property checks are addressed by ``name`` and grouped by
    ``target`` downstream. If later phases need to group results by suite,
    source file, or theme, this loader should be extended (e.g. to return
    ``list[tuple[SuiteMetadata, PropertyCheck]]`` or to carry the suite
    handle on ``PropertyCheck`` itself) without changing the existing
    YAML shapes.
    """
    path = Path(path)
    properties: list[PropertyCheck] = []
    for yaml_path in _yaml_files(path):
        data = _safe_load(yaml_path)
        if isinstance(data, dict) and "properties" in data:
            entries = data["properties"]
        elif isinstance(data, list):
            entries = data
        else:
            raise CorpusError(
                f"{yaml_path}: property-suite YAML must be either a list of "
                f"property dicts or a mapping with a 'properties' key; "
                f"got {type(data).__name__}"
            )
        if not isinstance(entries, list):
            raise CorpusError(
                f"{yaml_path}: 'properties' must be a list; got {type(entries).__name__}"
            )
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise CorpusError(
                    f"{yaml_path}: property entry #{i} must be a mapping; "
                    f"got {type(entry).__name__}"
                )
            try:
                properties.append(PropertyCheck.model_validate(entry))
            except ValueError as exc:
                raise CorpusError(f"{yaml_path} (entry #{i}): {exc}") from exc
    return properties
