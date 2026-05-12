"""Claude Code adapter.

Compiles a USCP manifest into a Claude Code custom slash-command Markdown file.
Claude Code reads custom commands from `.claude/commands/<name>.md`.
"""

from __future__ import annotations

from uscp.adapters.base import BaseAdapter


class ClaudeCodeAdapter(BaseAdapter):
    """Adapter for Anthropic Claude Code."""

    target_name = "claude-code"

    def output_filename(self) -> str:
        return f"{self.name}.md"

    def render(self) -> str:
        lines: list[str] = []

        # Front-matter comment block
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"> {self.description}")
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
            lines.append("## Examples")
            lines.append("")
            for ex in self.examples:
                lines.append(f"```")
                lines.append(ex)
                lines.append(f"```")
            lines.append("")

        # Workflow — this becomes the prompt body sent to Claude
        lines.append("## Instructions")
        lines.append("")
        lines.append(
            "You are executing the `/" + self.name + "` command. "
            "Follow these steps in order:"
        )
        lines.append("")
        for step_line in self._workflow_lines():
            lines.append(step_line)
        lines.append("")

        # Permissions note
        perms = self._manifest.get("permissions", {})
        fs = perms.get("filesystem", {})
        write_paths = fs.get("write", [])
        mode = self._manifest.get("execution", {}).get("mode", "analyze-only")
        lines.append("## Constraints")
        lines.append("")
        lines.append(f"- Execution mode: **{mode}**")
        if not write_paths:
            lines.append("- Do **not** modify any files.")
        else:
            lines.append(f"- You may only write to: `{'`, `'.join(write_paths)}`")
        network = perms.get("network", {}).get("allowed", False)
        if not network:
            lines.append("- Do **not** make network requests.")
        lines.append("")

        # Output contract
        output = self._manifest.get("output", {})
        sections = output.get("sections", [])
        if sections:
            lines.append("## Expected Output Sections")
            lines.append("")
            for s in sections:
                lines.append(f"- {s}")
            lines.append("")

        return "\n".join(lines)
