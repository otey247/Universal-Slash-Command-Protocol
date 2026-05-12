"""Cursor adapter.

Compiles a USCP manifest into a Cursor `.cursorrules` or prompt file.
Cursor reads custom instructions from `.cursorrules` or `.cursor/rules/<name>.mdc`.
"""

from __future__ import annotations

from uscp.adapters.base import BaseAdapter


class CursorAdapter(BaseAdapter):
    """Adapter for Cursor AI editor."""

    target_name = "cursor"

    def output_filename(self) -> str:
        return f"{self.name}.mdc"

    def render(self) -> str:
        lines: list[str] = []

        # Cursor MDC front-matter
        lines.append("---")
        lines.append(f"description: {self.description}")
        globs: list[str] = []
        read_paths = self._manifest.get("permissions", {}).get("filesystem", {}).get("read", [])
        if read_paths:
            # Convert USCP glob patterns to Cursor glob patterns
            for p in read_paths:
                if not p.startswith("${"):
                    globs.append(p)
        if globs:
            lines.append(f'globs: [{", ".join(globs)}]')
        mode = self._manifest.get("execution", {}).get("mode", "analyze-only")
        lines.append(f"alwaysApply: false")
        lines.append("---")
        lines.append("")

        # Command title and description
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(self.description)
        lines.append("")

        # Arguments
        arg_lines = self._arg_lines()
        if arg_lines:
            lines.append("## Arguments")
            lines.append("")
            lines.extend(arg_lines)
            lines.append("")

        # Examples
        if self.examples:
            lines.append("## Usage Examples")
            lines.append("")
            for ex in self.examples:
                lines.append(f"- `{ex}`")
            lines.append("")

        # Workflow
        lines.append("## Workflow")
        lines.append("")
        for step_line in self._workflow_lines():
            lines.append(step_line)
        lines.append("")

        # Constraints
        perms = self._manifest.get("permissions", {})
        write_paths = perms.get("filesystem", {}).get("write", [])
        shell_allowed = perms.get("shell", {}).get("allowed", [])
        lines.append("## Constraints")
        lines.append("")
        lines.append(f"- Execution mode: `{mode}`")
        if not write_paths:
            lines.append("- **Do not** create or modify files.")
        else:
            lines.append(f"- Write access limited to: `{'`, `'.join(write_paths)}`")
        if shell_allowed:
            lines.append(f"- Shell commands allowed: `{'`, `'.join(shell_allowed)}`")
        else:
            lines.append("- **Do not** run shell commands.")
        lines.append("")

        return "\n".join(lines)
