"""Command registry — discovers USCP manifests from the filesystem."""

from __future__ import annotations

import pathlib
from typing import Any

import yaml

# Standard locations USCP searches for command manifests, in priority order.
DISCOVERY_PATHS: list[str] = [
    ".agent/commands",
    ".github/commands",
    ".claude/commands",
    ".codex/commands",
    ".cursor/commands",
]


class CommandRegistry:
    """Discovers and indexes USCP command manifests from a project root."""

    def __init__(self, root: str | pathlib.Path = ".") -> None:
        self._root = pathlib.Path(root).resolve()
        self._commands: dict[str, dict[str, Any]] = {}
        self._paths: dict[str, pathlib.Path] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover(self, search_paths: list[str] | None = None) -> int:
        """Scan *search_paths* (or the standard USCP locations) for manifests.

        Parameters
        ----------
        search_paths:
            Override the default discovery paths. Relative to *root*.

        Returns
        -------
        int
            Number of manifests discovered.
        """
        paths = search_paths or DISCOVERY_PATHS
        found = 0
        for rel in paths:
            directory = self._root / rel
            if not directory.is_dir():
                continue
            for yaml_file in sorted(directory.glob("*.yaml")):
                try:
                    manifest = _load_yaml(yaml_file)
                    name = manifest.get("name")
                    if not name:
                        continue
                    self._commands[name] = manifest
                    self._paths[name] = yaml_file
                    found += 1
                except Exception:  # noqa: BLE001
                    pass
        return found

    def get(self, name: str) -> dict[str, Any] | None:
        """Return the manifest for command *name*, or ``None`` if not found."""
        return self._commands.get(name)

    def get_path(self, name: str) -> pathlib.Path | None:
        """Return the filesystem path for command *name*."""
        return self._paths.get(name)

    def list_commands(self) -> list[dict[str, Any]]:
        """Return all discovered manifests, sorted by name."""
        return [self._commands[k] for k in sorted(self._commands)]

    def resolve(self, invocation: str) -> dict[str, Any] | None:
        """Resolve a command name or alias to a manifest.

        Parameters
        ----------
        invocation:
            The command name as typed by the user (without leading slash).

        Returns
        -------
        dict or None
            The matching manifest, or ``None`` if not found.
        """
        # Direct name match
        if invocation in self._commands:
            return self._commands[invocation]
        # Alias match
        for manifest in self._commands.values():
            if invocation in manifest.get("aliases", []):
                return manifest
        return None

    @property
    def count(self) -> int:
        """Number of discovered commands."""
        return len(self._commands)


def _load_yaml(path: pathlib.Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
