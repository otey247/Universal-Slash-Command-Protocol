"""Tests for the uscp CLI."""

from __future__ import annotations

import pathlib
import shutil

import pytest
from click.testing import CliRunner

from uscp.cli import main

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
REPO_ROOT = pathlib.Path(__file__).parent.parent


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def temp_project(tmp_path):
    cmd_dir = tmp_path / ".agent" / "commands"
    cmd_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "valid_command.yaml", cmd_dir / "valid_command.yaml")
    shutil.copy(FIXTURES / "full_command.yaml", cmd_dir / "full_command.yaml")
    return tmp_path


class TestValidateCommand:
    def test_validate_valid_file_exits_zero(self, runner):
        result = runner.invoke(main, ["validate", str(FIXTURES / "valid_command.yaml")])
        assert result.exit_code == 0

    def test_validate_invalid_file_exits_nonzero(self, runner):
        result = runner.invoke(main, ["validate", str(FIXTURES / "invalid_command.yaml")])
        assert result.exit_code != 0

    def test_validate_dir_validates_all_files(self, runner):
        result = runner.invoke(main, ["validate", "--dir", str(FIXTURES)])
        # invalid_command.yaml is in fixtures, so this should exit non-zero
        assert result.exit_code != 0

    def test_validate_no_args_exits_nonzero(self, runner):
        result = runner.invoke(main, ["validate"])
        assert result.exit_code != 0

    def test_validate_bundled_review_api(self, runner):
        result = runner.invoke(
            main, ["validate", str(REPO_ROOT / ".agent" / "commands" / "review-api.yaml")]
        )
        assert result.exit_code == 0, result.output

    def test_validate_all_bundled_commands(self, runner):
        cmd_dir = REPO_ROOT / ".agent" / "commands"
        for yaml_file in sorted(cmd_dir.glob("*.yaml")):
            result = runner.invoke(main, ["validate", str(yaml_file)])
            assert result.exit_code == 0, f"{yaml_file.name}: {result.output}"


class TestListCommand:
    def test_list_shows_discovered_commands(self, runner, temp_project):
        result = runner.invoke(main, ["list", "--root", str(temp_project)])
        assert result.exit_code == 0
        assert "test-command" in result.output
        assert "full-command" in result.output

    def test_list_empty_project_exits_zero(self, runner, tmp_path):
        result = runner.invoke(main, ["list", "--root", str(tmp_path)])
        assert result.exit_code == 0

    def test_list_repo_shows_bundled_commands(self, runner):
        result = runner.invoke(main, ["list", "--root", str(REPO_ROOT)])
        assert result.exit_code == 0
        assert "review-api" in result.output
        assert "create-tests" in result.output


class TestCompileCommand:
    def test_compile_claude_code(self, runner, temp_project):
        result = runner.invoke(
            main,
            ["compile", "--target", "claude-code", "--root", str(temp_project), "--output",
             str(temp_project / "dist")],
        )
        assert result.exit_code == 0, result.output
        assert (temp_project / "dist" / "test-command.md").exists()

    def test_compile_specific_command_by_name(self, runner, temp_project):
        result = runner.invoke(
            main,
            [
                "compile",
                "--target", "codex",
                "--root", str(temp_project),
                "--output", str(temp_project / "dist"),
                "test-command",
            ],
        )
        assert result.exit_code == 0, result.output

    def test_compile_unknown_command_exits_nonzero(self, runner, temp_project):
        result = runner.invoke(
            main,
            [
                "compile",
                "--target", "claude-code",
                "--root", str(temp_project),
                "does-not-exist",
            ],
        )
        assert result.exit_code != 0

    def test_compile_all_targets(self, runner, temp_project):
        for target in ["claude-code", "codex", "vscode-copilot", "cursor"]:
            result = runner.invoke(
                main,
                [
                    "compile",
                    "--target", target,
                    "--root", str(temp_project),
                    "--output", str(temp_project / f"dist-{target}"),
                ],
            )
            assert result.exit_code == 0, f"Target {target}: {result.output}"


class TestInstallCommand:
    def test_install_valid_manifests(self, runner, tmp_path):
        dest = tmp_path / "installed"
        result = runner.invoke(
            main,
            ["install", str(FIXTURES), "--dest", str(dest)],
        )
        assert result.exit_code == 0
        # valid_command.yaml and full_command.yaml should be installed
        assert (dest / "valid_command.yaml").exists()
        assert (dest / "full_command.yaml").exists()

    def test_install_creates_dest_directory(self, runner, tmp_path):
        dest = tmp_path / "new" / "deep" / "dir"
        result = runner.invoke(
            main,
            ["install", str(FIXTURES), "--dest", str(dest)],
        )
        assert result.exit_code == 0
        assert dest.exists()

    def test_install_skips_invalid_manifests(self, runner, tmp_path):
        """invalid_command.yaml should be skipped but install should still succeed."""
        dest = tmp_path / "installed"
        result = runner.invoke(
            main,
            ["install", str(FIXTURES), "--dest", str(dest)],
        )
        assert result.exit_code == 0
        # invalid_command.yaml should NOT be installed
        assert not (dest / "invalid_command.yaml").exists()


class TestShowCommand:
    def test_show_existing_command(self, runner, temp_project):
        result = runner.invoke(
            main,
            ["show", "test-command", "--root", str(temp_project)],
        )
        assert result.exit_code == 0
        assert "test-command" in result.output

    def test_show_with_leading_slash(self, runner, temp_project):
        result = runner.invoke(
            main,
            ["show", "/test-command", "--root", str(temp_project)],
        )
        assert result.exit_code == 0

    def test_show_unknown_command_exits_nonzero(self, runner, tmp_path):
        result = runner.invoke(
            main,
            ["show", "nonexistent", "--root", str(tmp_path)],
        )
        assert result.exit_code != 0
