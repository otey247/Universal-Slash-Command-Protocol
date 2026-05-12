"""Tests for uscp.registry."""

from __future__ import annotations

import pathlib
import shutil

import pytest

from uscp.registry import CommandRegistry

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

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

    def test_discover_includes_cursor_rules_path(self, tmp_path):
        rules_dir = tmp_path / ".cursor" / "rules"
        rules_dir.mkdir(parents=True)
        shutil.copy(FIXTURES / "valid_command.yaml", rules_dir / "valid_command.yaml")

        registry = CommandRegistry(tmp_path)
        count = registry.discover()

        assert count == 1
        assert registry.get("test-command") is not None

    def test_discover_collects_yaml_errors(self, tmp_path):
        cmd_dir = tmp_path / ".agent" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "broken.yaml").write_text("name: [unterminated\n", encoding="utf-8")

        registry = CommandRegistry(tmp_path)
        count = registry.discover()

        assert count == 0
        assert registry.errors
        assert "broken.yaml" in registry.errors[0]
