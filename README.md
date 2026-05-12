# Universal Slash Command Protocol (USCP)

A universal slash-command protocol that treats slash commands as **portable workflow manifests** — not tool-specific prompt shortcuts.

## Overview

Every agentic coding environment is converging on the same pattern but with incompatible packaging. Claude Code, Codex CLI, GitHub Copilot, Cursor, Windsurf, Kiro, and others all support slash commands — but each one has its own format, its own prompt syntax, and its own notion of permissions and context.

**USCP defines a single declarative format** that any tool can understand:

```
/review-api --scope src/api --risk high --output markdown
```

This command behaves **consistently** across every supported agentic coding tool by compiling the universal manifest into each tool's native format.

---

## Quick Start

### Install the CLI

```bash
pip install uscp
```

### Discover commands in your project

```bash
uscp list
```

### Validate a manifest

```bash
uscp validate .agent/commands/review-api.yaml
```

### Compile to Claude Code format

```bash
uscp compile --target claude-code
```

### Compile to all supported targets

```bash
uscp compile --target codex
uscp compile --target vscode-copilot
uscp compile --target cursor
```

### Show command details

```bash
uscp show /review-api
```

### Install commands from another directory

```bash
uscp install /path/to/shared-commands/
```

---

## Protocol Architecture

```
User types:  /review-api src/api --risk high
                    │
                    ▼
         Command Registry
         (discovers .agent/commands/)
                    │
                    ▼
         Command Manifest (YAML)
         ┌─────────────────────────┐
         │ identity + version      │
         │ typed arguments         │
         │ required context        │
         │ permissions             │
         │ capability declarations │
         │ workflow steps          │
         │ output contract         │
         └─────────────────────────┘
                    │
            ┌───────┼───────┐
            ▼       ▼       ▼
       Claude    Codex    Cursor
        Code      CLI    / VS Code
        .md       .md     .mdc/.prompt.md
```

### Five Protocol Layers

| Layer | Responsibility |
|-------|---------------|
| **Discovery** | Find commands from `.agent/commands/`, `.github/commands/`, or MCP servers |
| **Manifest** | Declarative YAML spec: identity, args, context, permissions, workflow, output |
| **Invocation** | `/<command> [positional args] [--flags]` — parsed into a normalized envelope |
| **Execution** | Capability declarations map to host-specific tools and MCP primitives |
| **Output** | Both human-readable Markdown and machine-readable JSON |

---

## Command Manifest Format

Command manifests live in `.agent/commands/*.yaml` and validate against the [JSON Schema](schemas/command.v1.json).

### Minimal example

```yaml
schema: "https://universal-slash.dev/schemas/command.v1.json"
id: "com.company.review-api"
name: "review-api"
version: "1.0.0"
description: "Reviews API code for correctness and security."

arguments:
  type: object
  required: [scope]
  properties:
    scope:
      type: string
      description: "File or folder to review."

context:
  required: [repository, git_diff]

permissions:
  filesystem:
    read: ["${args.scope}"]
    write: []
  network:
    allowed: false

workflow:
  steps:
    - id: analyze
      instruction: "Analyze the target files for issues."
    - id: report
      instruction: "Produce a prioritized findings report."

output:
  format: "markdown"
  sections: ["Summary", "Findings", "Recommendations"]
```

### Full field reference

| Field | Required | Description |
|-------|----------|-------------|
| `schema` | ✅ | URI of the USCP JSON Schema |
| `id` | ✅ | Reverse-domain unique ID (e.g. `com.company.review-api`) |
| `name` | ✅ | Short command name used after `/` |
| `version` | ✅ | Semantic version (e.g. `1.0.0`) |
| `description` | ✅ | One-sentence description |
| `arguments` | ✅ | JSON Schema for command arguments |
| `context` | ✅ | Required/optional context items |
| `permissions` | ✅ | Filesystem, shell, network, secrets |
| `workflow` | ✅ | Ordered workflow steps |
| `output` | ✅ | Output format and schema |
| `title` | ○ | Human-readable title for tool UIs |
| `aliases` | ○ | Alternative command names |
| `examples` | ○ | Example invocations |
| `compatibility` | ○ | Supported tools and MCP version |
| `capabilities` | ○ | Universal capability declarations |
| `execution` | ○ | Mode, autonomy, confirmation policy, timeout |
| `mcp` | ○ | MCP prompt/resource/tool bindings |
| `policies` | ○ | References to org policy files |
| `telemetry` | ○ | Telemetry configuration |
| `lifecycle_hooks` | ○ | Pre/post/error hooks |

---

## Execution Modes

| Mode | Can Read | Can Propose | Can Write | Autonomy |
|------|----------|-------------|-----------|----------|
| `analyze-only` | ✅ | ❌ | ❌ | bounded |
| `propose-patch` | ✅ | ✅ | ❌ | supervised |
| `apply-patch` | ✅ | ✅ | ✅ | supervised |
| `autonomous` | ✅ | ✅ | ✅ | autonomous |

---

## Bundled Commands

This repository ships with five ready-to-use command manifests in [`.agent/commands/`](.agent/commands/):

### `/review-api`
Reviews API code for correctness, security (OWASP Top 10), observability, and contract alignment.

```
/review-api src/api --risk high
/review-api apps/backend/**/*.py --risk medium --output issues
```

### `/create-tests`
Generates comprehensive unit and integration tests for a target module.

```
/create-tests src/services/payment --framework pytest
/create-tests src/api/users.py --framework jest --type unit,integration
```

### `/write-adr`
Creates a well-structured Architecture Decision Record (ADR).

```
/write-adr "Use MCP for tool integration"
/write-adr "Migrate to GraphQL" --status proposed --supersedes ADR-003
```

### `/threat-model`
Performs a structured STRIDE threat-modeling analysis.

```
/threat-model apps/backend --auth oauth2
/threat-model src/payment --analysis stride
```

### `/prepare-pr`
Generates a comprehensive PR description, changelog entry, and pre-merge checklist.

```
/prepare-pr
/prepare-pr --type feature --ticket PROJ-1234
```

---

## Adapter Architecture

Each agentic coding tool gets a small adapter that translates the universal manifest into its native format:

| Target | Flag | Output |
|--------|------|--------|
| Claude Code | `--target claude-code` | `.claude/commands/<name>.md` |
| Codex CLI | `--target codex` | `.codex/commands/<name>.md` |
| VS Code Copilot | `--target vscode-copilot` | `<name>.prompt.md` |
| Cursor | `--target cursor` | `<name>.mdc` |

```bash
# Compile all commands for Claude Code
uscp compile --target claude-code --output .claude/commands/

# Compile a single command for Cursor
uscp compile --target cursor --output .cursor/rules/ review-api
```

---

## Capability Mapping

Commands declare **universal capabilities** that each host maps to its own tools:

| Universal Capability | Claude Code | Codex CLI | VS Code Copilot | Cursor |
|---------------------|-------------|-----------|-----------------|--------|
| `filesystem.read` | File read | File read | Workspace API | Context |
| `filesystem.write` | Edit tool | Write tool | Edit API | Edit |
| `git.diff` | Shell/git | Git context | Source control | Git |
| `tests.run` | Bash tool | Sandbox | Task runner | Terminal |
| `mcp.tool.invoke` | MCP tool | MCP tool | MCP server | MCP server |

---

## Permissions Model

Commands declare **least-privilege permissions**:

```yaml
permissions:
  filesystem:
    read: ["src/**", "tests/**"]
    write: ["tests/**"]
  shell:
    allowed: ["pytest", "npm test"]
    denied: ["rm", "curl", "ssh"]
  network:
    allowed: false
  secrets:
    access: false
```

---

## MCP Integration

USCP **extends** MCP — it does not compete with it. Commands map to MCP primitives:

```yaml
mcp:
  prompt: "company.review-api"
  resources:
    - "repo://current"
    - "git://diff"
  tools:
    - "filesystem.read"
    - "git.diff"
```

Any MCP-compatible tool can discover and invoke USCP commands as structured prompts.

---

## Project Structure

```
.
├── schemas/
│   └── command.v1.json          # JSON Schema for manifest validation
├── .agent/
│   ├── commands/                 # Universal command manifests
│   │   ├── review-api.yaml
│   │   ├── create-tests.yaml
│   │   ├── write-adr.yaml
│   │   ├── threat-model.yaml
│   │   └── prepare-pr.yaml
│   ├── policies/                 # Org-level policy files
│   │   ├── permissions.yaml
│   │   ├── coding-standards.yaml
│   │   └── security-baseline.yaml
│   └── context/                  # Context documents for agent commands
│       ├── architecture.md
│       ├── definition-of-done.md
│       └── testing-strategy.md
├── src/uscp/                     # Python CLI package
│   ├── cli.py                    # uscp CLI (validate, list, compile, install, show)
│   ├── validator.py              # JSON Schema validation
│   ├── compiler.py               # Manifest-to-adapter compilation
│   ├── registry.py               # Command discovery
│   └── adapters/                 # Tool-specific adapters
│       ├── claude_code.py
│       ├── codex.py
│       ├── vscode_copilot.py
│       └── cursor.py
└── tests/                        # Test suite (93 tests)
```

---

## Development

```bash
# Clone and install
git clone https://github.com/otey247/Universal-Slash-Command-Protocol
cd Universal-Slash-Command-Protocol
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=uscp --cov-report=term-missing

# Validate all bundled commands
uscp validate --dir .agent/commands/
```

---

## Why USCP?

Instead of maintaining separate prompt files for each tool:

| Without USCP | With USCP |
|-------------|-----------|
| `claude/review-api.md` | `.agent/commands/review-api.yaml` |
| `codex/review-api.md` | (same file) |
| `copilot/review-api.prompt.md` | (same file) |
| `cursor/review-api.mdc` | (same file) |

One enterprise command library. Many agentic coding tools. Consistent behavior, governance, and outputs.

---

## License

MIT
