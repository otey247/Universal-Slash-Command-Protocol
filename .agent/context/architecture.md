# Architecture Context
# This file is injected as context for architectural commands (/write-adr, /threat-model, /review-api).

## System Overview

This repository implements the Universal Slash Command Protocol (USCP) — a portable,
declarative specification for agentic workflow commands that work consistently across
multiple AI coding tools.

## Key Components

- **Command Manifest** (`.agent/commands/*.yaml`): Declarative workflow specifications
  validated against the USCP JSON Schema.
- **JSON Schema** (`schemas/command.v1.json`): The authoritative schema for command manifests.
- **CLI Tool** (`uscp`): Python CLI for discovering, validating, and compiling commands.
- **Adapters** (`src/uscp/adapters/`): Tool-specific output compilers.

## Design Principles

1. Commands are portable workflow contracts, not prompt snippets.
2. Least-privilege permissions declared per command.
3. Context is explicitly declared, not assumed.
4. Output is both human and machine-readable.
5. MCP is the integration layer, not the replacement.

## Decision Log

See `docs/adr/` for Architecture Decision Records.
