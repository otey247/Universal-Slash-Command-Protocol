# Definition of Done

A USCP command manifest is considered complete when:

## Schema Compliance
- [ ] Validates against `schemas/command.v1.json` without errors
- [ ] All required fields are present: `schema`, `id`, `name`, `version`, `description`,
      `arguments`, `context`, `permissions`, `workflow`, `output`

## Argument Quality
- [ ] Every argument has a `type` and `description`
- [ ] Required arguments are listed under `arguments.required`
- [ ] Default values specified for optional arguments where applicable
- [ ] At least one `example` value provided per argument

## Security
- [ ] `permissions` section follows least-privilege principle
- [ ] `write: []` for read-only commands
- [ ] `network.allowed: false` unless explicitly needed
- [ ] `secrets.access: false` unless explicitly needed

## Workflow
- [ ] At least two workflow steps
- [ ] Each step has a clear, actionable `instruction`
- [ ] Step IDs use lowercase kebab-case

## Output
- [ ] `output.format` declared
- [ ] `output.sections` listed for markdown output
- [ ] `output.machine_readable` schema defined

## Documentation
- [ ] At least two `examples` in the top-level `examples` field
- [ ] `title` is human-readable and suitable for UI display
- [ ] `description` is a single clear sentence
