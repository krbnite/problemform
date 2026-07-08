"""Default rubric / property-suite resolution for ``problemform benchmark``.

When the ``benchmark`` command is invoked without explicit ``--rubric`` /
``--property-suite`` flags, it falls back to the project's shipped defaults under
``benchmarks/rubrics/`` and ``benchmarks/properties/``. Paths are resolved from
this module's location (``<repo>/problemform/eval/defaults.py``) rather than the
current working directory, so the defaults load regardless of where the CLI is
invoked. The only supported install is editable (``pip install -e .``), so this
repo-relative layout is stable.

Loaders return ``[]`` (with a caller-visible reason) rather than raising when a
default directory is absent — a benchmark should still run with whatever lenses
are available.
"""

from __future__ import annotations

from pathlib import Path

from problemform.eval.corpus import CorpusError, load_property_suite, load_rubrics
from problemform.eval.models import PropertyCheck, Rubric

_REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_RUBRICS_DIR = _REPO_ROOT / "benchmarks" / "rubrics"
DEFAULT_PROPERTIES_DIR = _REPO_ROOT / "benchmarks" / "properties"


def load_default_rubrics() -> tuple[list[Rubric], str | None]:
    """Load the shipped default rubrics; return ``([], reason)`` if unavailable."""
    if not DEFAULT_RUBRICS_DIR.exists():
        return [], f"default rubrics dir not found: {DEFAULT_RUBRICS_DIR}"
    try:
        return load_rubrics(DEFAULT_RUBRICS_DIR), None
    except CorpusError as exc:
        return [], f"failed to load default rubrics: {exc}"


def load_default_properties() -> tuple[list[PropertyCheck], str | None]:
    """Load the shipped default property suites; return ``([], reason)`` if unavailable."""
    if not DEFAULT_PROPERTIES_DIR.exists():
        return [], f"default properties dir not found: {DEFAULT_PROPERTIES_DIR}"
    try:
        return load_property_suite(DEFAULT_PROPERTIES_DIR), None
    except CorpusError as exc:
        return [], f"failed to load default properties: {exc}"
