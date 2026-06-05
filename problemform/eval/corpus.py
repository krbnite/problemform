"""YAML corpus loader for evaluation test cases.

See `docs/designs/milestone_03_evaluation_framework.md` Section 4 for the
directory convention. Each YAML file is one ``TestCase``. The loader walks a
suite directory recursively so users can organize cases into category subdirs
without the loader needing to know about them.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from problemform.eval.models import TestCase


class CorpusError(ValueError):
    """Raised when a test-case YAML file cannot be loaded or validated."""


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
        try:
            data = yaml.safe_load(path.read_text())
        except yaml.YAMLError as exc:
            raise CorpusError(f"failed to parse YAML at {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise CorpusError(
                f"{path}: top-level must be a mapping; got {type(data).__name__}"
            )
        try:
            cases.append(TestCase.model_validate(data))
        except ValueError as exc:
            raise CorpusError(f"{path}: {exc}") from exc
    return cases
