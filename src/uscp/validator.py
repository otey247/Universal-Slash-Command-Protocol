"""Command manifest validator.

Loads and validates USCP command manifests against the JSON Schema.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import jsonschema
import yaml

# Path to the bundled schema file, relative to this package.
_SCHEMA_PATH = pathlib.Path(__file__).parent.parent.parent / "schemas" / "command.v1.json"


def _load_schema() -> dict[str, Any]:
    """Load the bundled USCP JSON Schema."""
    with _SCHEMA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_manifest(path: str | pathlib.Path) -> dict[str, Any]:
    """Load a YAML command manifest from *path*.

    Parameters
    ----------
    path:
        Filesystem path to a ``.yaml`` manifest file.

    Returns
    -------
    dict
        Parsed manifest as a Python dictionary.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    yaml.YAMLError
        If the file cannot be parsed as YAML.
    """
    path = pathlib.Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate(manifest: dict[str, Any]) -> list[str]:
    """Validate *manifest* against the USCP JSON Schema.

    Parameters
    ----------
    manifest:
        Parsed command manifest dictionary (as returned by :func:`load_manifest`).

    Returns
    -------
    list[str]
        A list of human-readable validation error messages. An empty list means
        the manifest is valid.
    """
    schema = _load_schema()
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))
    return [_format_error(e) for e in errors]


def validate_file(path: str | pathlib.Path) -> list[str]:
    """Load and validate a manifest file in one step.

    Parameters
    ----------
    path:
        Filesystem path to a ``.yaml`` manifest file.

    Returns
    -------
    list[str]
        Validation error messages (empty = valid).
    """
    manifest = load_manifest(path)
    return validate(manifest)


def _format_error(error: jsonschema.ValidationError) -> str:
    """Format a :class:`jsonschema.ValidationError` as a readable string."""
    path = " → ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
    return f"[{path}] {error.message}"
