# Testing Strategy

## Philosophy

USCP commands that generate or transform code must produce tests that follow the
testing pyramid: 70% unit, 20% integration, 10% end-to-end.

## Test Naming Convention

```
test_<subject>_<condition>_<expected_result>
```

Examples:
- `test_validate_manifest_missing_required_field_raises_error`
- `test_compile_review_api_to_claude_code_produces_md_file`
- `test_registry_discover_commands_from_agent_dir`

## Test Location

Mirror the source structure under `tests/`:
- `src/uscp/validator.py` → `tests/test_validator.py`
- `src/uscp/compiler.py` → `tests/test_compiler.py`
- `src/uscp/adapters/*.py` → `tests/adapters/test_adapters.py` (combined adapter coverage)

## Required Coverage

- Minimum 80% line coverage for all `src/uscp/` modules
- 100% coverage of the JSON Schema (all required/optional fields)
- All adapters must have at least one integration test

## Test Data

Reference test fixtures live in `tests/fixtures/`:
- `valid_command.yaml` — minimal valid command manifest
- `invalid_command.yaml` — manifest missing required fields
- `full_command.yaml` — manifest exercising every optional field
