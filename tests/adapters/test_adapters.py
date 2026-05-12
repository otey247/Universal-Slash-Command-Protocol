"""Tests for individual adapters."""

from __future__ import annotations

import pathlib

import pytest
import yaml

from uscp import validator as val
from uscp.adapters.claude_code import ClaudeCodeAdapter
from uscp.adapters.codex import CodexAdapter
from uscp.adapters.cursor import CursorAdapter
from uscp.adapters.vscode_copilot import VSCodeCopilotAdapter

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"


@pytest.fixture()
def valid_manifest():
    return val.load_manifest(FIXTURES / "valid_command.yaml")


@pytest.fixture()
def full_manifest():
    return val.load_manifest(FIXTURES / "full_command.yaml")


class TestClaudeCodeAdapter:
    def test_render_contains_title(self, valid_manifest):
        rendered = ClaudeCodeAdapter(valid_manifest).render()
        assert "Test Command" in rendered

    def test_render_contains_instructions_section(self, valid_manifest):
        rendered = ClaudeCodeAdapter(valid_manifest).render()
        assert "## Instructions" in rendered

    def test_render_contains_constraints_section(self, valid_manifest):
        rendered = ClaudeCodeAdapter(valid_manifest).render()
        assert "## Constraints" in rendered

    def test_render_read_only_includes_no_modify_note(self, valid_manifest):
        rendered = ClaudeCodeAdapter(valid_manifest).render()
        assert "not" in rendered.lower() and "modif" in rendered.lower()

    def test_output_filename_ends_with_md(self, valid_manifest):
        adapter = ClaudeCodeAdapter(valid_manifest)
        assert adapter.output_filename().endswith(".md")
        assert "test-command" in adapter.output_filename()

    def test_write_creates_file(self, valid_manifest, tmp_path):
        adapter = ClaudeCodeAdapter(valid_manifest)
        path = adapter.write(tmp_path)
        assert path.exists()
        assert path.read_text()


class TestCodexAdapter:
    def test_render_contains_task_section(self, valid_manifest):
        rendered = CodexAdapter(valid_manifest).render()
        assert "## Task" in rendered

    def test_render_contains_parameters_when_args_present(self, valid_manifest):
        rendered = CodexAdapter(valid_manifest).render()
        assert "## Parameters" in rendered

    def test_render_full_manifest(self, full_manifest):
        rendered = CodexAdapter(full_manifest).render()
        assert "full-command" in rendered.lower() or "Full Feature Command" in rendered

    def test_output_filename_ends_with_md(self, valid_manifest):
        assert CodexAdapter(valid_manifest).output_filename().endswith(".md")


class TestVSCodeCopilotAdapter:
    def test_render_starts_with_front_matter(self, valid_manifest):
        rendered = VSCodeCopilotAdapter(valid_manifest).render()
        assert rendered.startswith("---")

    def test_render_contains_description_in_front_matter(self, valid_manifest):
        rendered = VSCodeCopilotAdapter(valid_manifest).render()
        assert "description:" in rendered

    def test_render_contains_steps_section(self, valid_manifest):
        rendered = VSCodeCopilotAdapter(valid_manifest).render()
        assert "## Steps" in rendered

    def test_output_filename_ends_with_prompt_md(self, valid_manifest):
        assert VSCodeCopilotAdapter(valid_manifest).output_filename().endswith(".prompt.md")

    def test_render_output_structure_present_for_markdown_output(self, valid_manifest):
        rendered = VSCodeCopilotAdapter(valid_manifest).render()
        assert "## Output Structure" in rendered

    def test_render_front_matter_is_valid_yaml(self, valid_manifest):
        valid_manifest["description"] = 'Quotes: "double", colon: value\nSecond line'

        rendered = VSCodeCopilotAdapter(valid_manifest).render()
        front_matter = rendered.split("---", maxsplit=2)[1]
        metadata = yaml.safe_load(front_matter)

        assert metadata["description"] == valid_manifest["description"]
        assert metadata["mode"] == "agent"


class TestCursorAdapter:
    def test_render_starts_with_front_matter(self, valid_manifest):
        rendered = CursorAdapter(valid_manifest).render()
        assert rendered.startswith("---")

    def test_render_contains_always_apply(self, valid_manifest):
        rendered = CursorAdapter(valid_manifest).render()
        assert "alwaysApply" in rendered

    def test_render_contains_workflow_section(self, valid_manifest):
        rendered = CursorAdapter(valid_manifest).render()
        assert "## Workflow" in rendered

    def test_render_contains_constraints_section(self, valid_manifest):
        rendered = CursorAdapter(valid_manifest).render()
        assert "## Constraints" in rendered

    def test_output_filename_ends_with_mdc(self, valid_manifest):
        assert CursorAdapter(valid_manifest).output_filename().endswith(".mdc")

    def test_render_front_matter_quotes_yaml_sensitive_globs(self, valid_manifest):
        valid_manifest["permissions"]["filesystem"]["read"] = ["**/*.py", "docs/**"]
        valid_manifest["description"] = "Description: with colon"

        rendered = CursorAdapter(valid_manifest).render()
        front_matter = rendered.split("---", maxsplit=2)[1]
        metadata = yaml.safe_load(front_matter)

        assert metadata["description"] == valid_manifest["description"]
        assert metadata["globs"] == ["**/*.py", "docs/**"]
