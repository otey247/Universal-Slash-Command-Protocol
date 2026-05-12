"""Tests for uscp.registry."""

from __future__ import annotations

import pathlib
import shutil
import tempfile

import pytest
import yaml

from uscp.registry import CommandRegistry

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _write_temp_manifest(directory: pathlib.Path, name: str, content: dict) -> pathlib.Path:
    path = directory / f"{name}.yaml"
    with path.open("w", encoding="utf-8") as fh:
        yaml.dump(content, fh)
    return path


@pytest.fixture()
def temp_project(tmp_path):
    """A temporary project directory with .agent/commands/ populated."""
    cmd_dir = tmp_path / ".agent" / "commands"
    cmd_dir.mkdir(parents=True)
    # Copy fixtures
    shutil.copy(FIXTURES / "valid_command.yaml", cmd_dir / "valid_command.yaml")
    shutil.copy(FIXTURES / "full_command.yaml", cmd_dir / "full_command.yaml")
    return tmp_path


class TestCommandRegistry:
    def test_discover_finds_commands_in_agent_dir(self, temp_project):
        registry = CommandRegistry(temp_project)
        count = registry.discover()
        assert count == 2

    def test_discover_returns_zero_for_empty_project(self, tmp_path):
        registry = CommandRegistry(tmp_path)
        count = registry.discover()
        assert count == 0

    def test_get_returns_manifest_by_name(self, temp_project):
        registry = CommandRegistry(temp_project)
        registry.discover()
        manifest = registry.get("test-command")
        assert manifest is not None
        assert manifest["name"] == "test-command"

    def test_get_returns_none_for_unknown_name(self, temp_project):
        registry = CommandRegistry(temp_project)
        registry.discover()
        assert registry.get("does-not-exist") is None

    def test_get_path_returns_file_path(self, temp_project):
        registry = CommandRegistry(temp_project)
        registry.discover()
        path = registry.get_path("test-command")
        assert path is not None
        assert path.exists()

    def test_list_commands_sorted(self, temp_project):
        registry = CommandRegistry(temp_project)
        registry.discover()
        names = [m["name"] for m in registry.list_commands()]
        assert names == sorted(names)

    def test_resolve_by_name(self, temp_project):
        registry = CommandRegistry(temp_project)
        registry.discover()
        manifest = registry.resolve("test-command")
        assert manifest is not None

    def test_resolve_by_alias(self, temp_project):
        """full-command has aliases 'fc' and 'full'."""
        registry = CommandRegistry(temp_project)
        registry.discover()
        manifest = registry.resolve("fc")
        assert manifest is not None
        assert manifest["name"] == "full-command"

    def test_resolve_unknown_returns_none(self, temp_project):
        registry = CommandRegistry(temp_project)
        registry.discover()
        assert registry.resolve("unknown-alias") is None

    def test_count_property(self, temp_project):
        registry = CommandRegistry(temp_project)
        registry.discover()
        assert registry.count == 2

    def test_discover_real_agent_commands(self):
        """Discover the real .agent/commands/ in this repository."""
        repo_root = pathlib.Path(__file__).parent.parent
        registry = CommandRegistry(repo_root)
        count = registry.discover()
        assert count >= 5  # review-api, create-tests, write-adr, threat-model, prepare-pr
