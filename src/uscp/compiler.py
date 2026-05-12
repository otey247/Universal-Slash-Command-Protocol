"""Compiler — orchestrates manifest-to-adapter compilation."""

from __future__ import annotations

import pathlib
from typing import Any

from uscp.adapters import ADAPTERS, BaseAdapter


class CompilationResult:
    """Holds the result of compiling one manifest to one target."""

    def __init__(
        self,
        command_name: str,
        target: str,
        output_path: pathlib.Path | None,
        error: str | None = None,
    ) -> None:
        self.command_name = command_name
        self.target = target
        self.output_path = output_path
        self.error = error

    @property
    def success(self) -> bool:
        return self.error is None


def compile_manifest(
    manifest: dict[str, Any],
    target: str,
    output_dir: str | pathlib.Path,
) -> CompilationResult:
    """Compile one manifest to a tool-specific format.

    Parameters
    ----------
    manifest:
        Parsed USCP command manifest.
    target:
        Target tool identifier (e.g. ``"claude-code"``, ``"codex"``).
    output_dir:
        Directory where the output file will be written.

    Returns
    -------
    CompilationResult
        Result object with ``success``, ``output_path``, and ``error`` fields.
    """
    adapter_class = ADAPTERS.get(target)
    if adapter_class is None:
        known = ", ".join(sorted(ADAPTERS))
        return CompilationResult(
            command_name=manifest.get("name", "?"),
            target=target,
            output_path=None,
            error=f"Unknown target '{target}'. Known targets: {known}",
        )

    adapter: BaseAdapter = adapter_class(manifest)
    try:
        out_path = adapter.write(output_dir)
        return CompilationResult(
            command_name=manifest.get("name", "?"),
            target=target,
            output_path=out_path,
        )
    except Exception as exc:  # noqa: BLE001
        return CompilationResult(
            command_name=manifest.get("name", "?"),
            target=target,
            output_path=None,
            error=str(exc),
        )


def compile_manifests(
    manifests: list[dict[str, Any]],
    target: str,
    output_dir: str | pathlib.Path,
) -> list[CompilationResult]:
    """Compile a list of manifests to the same target.

    Parameters
    ----------
    manifests:
        List of parsed USCP command manifests.
    target:
        Target tool identifier.
    output_dir:
        Directory where output files will be written.

    Returns
    -------
    list[CompilationResult]
        One result per manifest.
    """
    return [compile_manifest(m, target, output_dir) for m in manifests]


def list_targets() -> list[str]:
    """Return the list of all supported target tool identifiers."""
    return sorted(ADAPTERS)
