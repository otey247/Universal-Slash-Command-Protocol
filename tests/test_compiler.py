"""Tests for uscp.compiler."""

from __future__ import annotations

import pathlib

import pytest

from uscp import compiler as comp
from uscp import validator as val
from uscp.compiler import list_targets

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture()
def valid_manifest():
    return val.load_manifest(FIXTURES / "valid_command.yaml")


@pytest.fixture()
def full_manifest():
    return val.load_manifest(FIXTURES / "full_command.yaml")


class TestListTargets:
    def test_returns_non_empty_list(self):
        targets = list_targets()
        assert len(targets) > 0

    def test_contains_expected_targets(self):
        targets = list_targets()
        assert "claude-code" in targets
        assert "codex" in targets
        assert "vscode-copilot" in targets
        assert "cursor" in targets


class TestCompileManifest:
    @pytest.mark.parametrize("target", list_targets())
    def test_compile_valid_manifest_succeeds(self, valid_manifest, tmp_path, target):
        result = comp.compile_manifest(valid_manifest, target, tmp_path)
        assert result.success, f"Compilation failed for {target}: {result.error}"
        assert result.output_path is not None
        assert result.output_path.exists()

    @pytest.mark.parametrize("target", list_targets())
    def test_compile_full_manifest_succeeds(self, full_manifest, tmp_path, target):
        result = comp.compile_manifest(full_manifest, target, tmp_path)
        assert result.success, f"Compilation failed for {target}: {result.error}"

    def test_compile_unknown_target_fails(self, valid_manifest, tmp_path):
        result = comp.compile_manifest(valid_manifest, "nonexistent-tool", tmp_path)
        assert not result.success
        assert result.error is not None
        assert "nonexistent-tool" in result.error

    def test_compile_creates_output_file(self, valid_manifest, tmp_path):
        result = comp.compile_manifest(valid_manifest, "claude-code", tmp_path)
        assert result.success
        assert result.output_path.stat().st_size > 0

    def test_compile_output_contains_command_name(self, valid_manifest, tmp_path):
        result = comp.compile_manifest(valid_manifest, "claude-code", tmp_path)
        content = result.output_path.read_text(encoding="utf-8")
        assert "test-command" in content

    def test_compile_result_has_command_name(self, valid_manifest, tmp_path):
        result = comp.compile_manifest(valid_manifest, "codex", tmp_path)
        assert result.command_name == "test-command"
        assert result.target == "codex"


class TestCompileManifests:
    def test_compile_multiple_manifests(self, valid_manifest, full_manifest, tmp_path):
        results = comp.compile_manifests([valid_manifest, full_manifest], "claude-code", tmp_path)
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_compile_empty_list_returns_empty(self, tmp_path):
        results = comp.compile_manifests([], "claude-code", tmp_path)
        assert results == []


class TestAdapterOutput:
    """Spot-check rendered output for each adapter."""

    def test_claude_code_output_has_instructions_section(self, valid_manifest, tmp_path):
        result = comp.compile_manifest(valid_manifest, "claude-code", tmp_path)
        content = result.output_path.read_text()
        assert "## Instructions" in content

    def test_codex_output_has_task_section(self, valid_manifest, tmp_path):
        result = comp.compile_manifest(valid_manifest, "codex", tmp_path)
        content = result.output_path.read_text()
        assert "## Task" in content

    def test_vscode_copilot_output_has_front_matter(self, valid_manifest, tmp_path):
        result = comp.compile_manifest(valid_manifest, "vscode-copilot", tmp_path)
        content = result.output_path.read_text()
        assert content.startswith("---")
        assert "description:" in content

    def test_vscode_copilot_output_filename_ends_with_prompt_md(self, valid_manifest, tmp_path):
        result = comp.compile_manifest(valid_manifest, "vscode-copilot", tmp_path)
        assert str(result.output_path).endswith(".prompt.md")

    def test_cursor_output_has_front_matter(self, valid_manifest, tmp_path):
        result = comp.compile_manifest(valid_manifest, "cursor", tmp_path)
        content = result.output_path.read_text()
        assert content.startswith("---")

    def test_cursor_output_filename_ends_with_mdc(self, valid_manifest, tmp_path):
        result = comp.compile_manifest(valid_manifest, "cursor", tmp_path)
        assert str(result.output_path).endswith(".mdc")
