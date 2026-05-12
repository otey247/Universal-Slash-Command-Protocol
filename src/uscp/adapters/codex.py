"""Codex CLI adapter.

Compiles a USCP manifest into a Codex CLI custom prompt Markdown file.
Codex reads custom prompts from `.codex/commands/<name>.md`.
"""

from __future__ import annotations

from uscp.adapters.base import BaseAdapter


class CodexAdapter(BaseAdapter):
    """Adapter for OpenAI Codex CLI."""

    target_name = "codex"

    def output_filename(self) -> str:
        return f"{self.name}.md"

    def render(self) -> str:
        lines: list[str] = []

        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(self.description)
        lines.append("")

        # Arguments table
        props = self.arguments.get("properties", {})
        required = self.arguments.get("required", [])
        if props:
            lines.append("## Parameters")
            lines.append("")
            lines.append("| Argument | Type | Required | Description |")
            lines.append("|----------|------|----------|-------------|")
            for arg_name, arg_def in props.items():
                req = "Yes" if arg_name in required else "No"
                arg_type = arg_def.get("type", "string")
                desc = arg_def.get("description", "")
                enum_vals = arg_def.get("enum")
                if enum_vals:
                    desc += f" Options: {', '.join(str(v) for v in enum_vals)}."
                default = arg_def.get("default")
                if default is not None:
                    desc += f" Default: `{default}`."
                lines.append(f"| `{arg_name}` | {arg_type} | {req} | {desc} |")
            lines.append("")

        # Usage examples
        if self.examples:
            lines.append("## Usage")
            lines.append("")
            lines.append("```")
            for ex in self.examples:
                lines.append(ex)
            lines.append("```")
            lines.append("")

        # Workflow steps become the system prompt
        lines.append("## Task")
        lines.append("")
        lines.append("Complete the following steps:")
        lines.append("")
        for step_line in self._workflow_lines():
            lines.append(step_line)
        lines.append("")

        # Safety constraints
        mode = self._manifest.get("execution", {}).get("mode", "analyze-only")
        perms = self._manifest.get("permissions", {})
        write_paths = perms.get("filesystem", {}).get("write", [])
        lines.append("## Safety")
        lines.append("")
        lines.append(f"Mode: `{mode}`")
        if not write_paths:
            lines.append("")
            lines.append("This command is **read-only**. Do not create or modify files.")
        lines.append("")

        return "\n".join(lines)
