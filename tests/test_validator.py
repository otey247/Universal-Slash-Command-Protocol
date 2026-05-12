"""Tests for uscp.validator."""

from __future__ import annotations

import pathlib

import pytest

from uscp import validator as val

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


class TestLoadManifest:
    def test_load_valid_yaml_returns_dict(self):
        manifest = val.load_manifest(FIXTURES / "valid_command.yaml")
        assert isinstance(manifest, dict)
        assert manifest["name"] == "test-command"

    def test_load_nonexistent_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            val.load_manifest(pathlib.Path("/nonexistent/path/command.yaml"))

    def test_load_full_command_yaml(self):
        manifest = val.load_manifest(FIXTURES / "full_command.yaml")
        assert manifest["id"] == "org.uscp.full-command"
        assert manifest["version"] == "2.1.0"

    def test_load_empty_yaml_returns_empty_dict(self, tmp_path):
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding="utf-8")

        manifest = val.load_manifest(path)

        assert manifest == {}

    def test_load_non_mapping_yaml_raises_type_error(self, tmp_path):
        path = tmp_path / "list.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")

        with pytest.raises(TypeError):
            val.load_manifest(path)


class TestValidate:
    def test_validate_valid_manifest_returns_empty_list(self):
        manifest = val.load_manifest(FIXTURES / "valid_command.yaml")
        errors = val.validate(manifest)
        assert errors == []

    def test_validate_full_manifest_returns_empty_list(self):
        manifest = val.load_manifest(FIXTURES / "full_command.yaml")
        errors = val.validate(manifest)
        assert errors == []

    def test_validate_invalid_manifest_returns_errors(self):
        manifest = val.load_manifest(FIXTURES / "invalid_command.yaml")
        errors = val.validate(manifest)
        assert len(errors) > 0

    def test_validate_missing_required_fields_reported(self):
        manifest = val.load_manifest(FIXTURES / "invalid_command.yaml")
        errors = val.validate(manifest)
        # Should flag missing: arguments, context, permissions, workflow, output
        combined = " ".join(errors)
        assert "arguments" in combined or "required" in combined.lower()

    def test_validate_empty_dict_returns_errors(self):
        errors = val.validate({})
        assert len(errors) > 0

    def test_validate_non_mapping_returns_clear_error(self):
        errors = val.validate(["not", "a", "mapping"])
        assert errors == ["[root] Manifest must be a mapping/object."]

    def test_validate_wrong_schema_uri_returns_error(self):
        manifest = val.load_manifest(FIXTURES / "valid_command.yaml")
        manifest["schema"] = "https://wrong.schema/v99.json"
        errors = val.validate(manifest)
        assert len(errors) > 0

    def test_validate_invalid_id_format(self):
        manifest = val.load_manifest(FIXTURES / "valid_command.yaml")
        manifest["id"] = "InvalidID_With_Uppercase"
        errors = val.validate(manifest)
        assert len(errors) > 0

    def test_validate_invalid_version_format(self):
        manifest = val.load_manifest(FIXTURES / "valid_command.yaml")
        manifest["version"] = "not-semver"
        errors = val.validate(manifest)
        assert len(errors) > 0

    def test_validate_invalid_execution_mode(self):
        manifest = val.load_manifest(FIXTURES / "valid_command.yaml")
        manifest["execution"] = {"mode": "explode-everything"}
        errors = val.validate(manifest)
        assert len(errors) > 0

    def test_validate_workflow_must_have_steps(self):
        manifest = val.load_manifest(FIXTURES / "valid_command.yaml")
        manifest["workflow"] = {"steps": []}
        errors = val.validate(manifest)
        assert len(errors) > 0


class TestValidateFile:
    def test_validate_file_valid(self):
        errors = val.validate_file(FIXTURES / "valid_command.yaml")
        assert errors == []

    def test_validate_file_invalid(self):
        errors = val.validate_file(FIXTURES / "invalid_command.yaml")
        assert len(errors) > 0

    def test_validate_file_full(self):
        errors = val.validate_file(FIXTURES / "full_command.yaml")
        assert errors == []

    def test_validate_file_non_mapping_returns_error(self, tmp_path):
        path = tmp_path / "list.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")

        errors = val.validate_file(path)

        assert len(errors) == 1
        assert "Manifest must be a YAML mapping/object" in errors[0]


class TestValidateRealCommands:
    """Validate the bundled .agent/commands/ manifests."""

    @pytest.fixture(params=list(
        (pathlib.Path(__file__).parent.parent / ".agent" / "commands").glob("*.yaml")
    ))
    def agent_command(self, request):
        return request.param

    def test_bundled_commands_are_valid(self, agent_command):
        errors = val.validate_file(agent_command)
        assert errors == [], f"{agent_command.name}: {errors}"
