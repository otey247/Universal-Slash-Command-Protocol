"""VS Code Copilot adapter.

Compiles a USCP manifest into a VS Code Copilot prompt file.
VS Code Copilot reads prompt files from `.github/copilot/prompts/<name>.prompt.md`
or `.copilot/prompts/<name>.prompt.md`.
"""

from __future__ import annotations

from uscp.adapters.base import BaseAdapter


class VSCodeCopilotAdapter(BaseAdapter):
    """Adapter for GitHub Copilot in VS Code."""

    target_name = "vscode-copilot"

    def output_filename(self) -> str:
        return f"{self.name}.prompt.md"

    def render(self) -> str:
        lines: list[str] = []

        # VS Code prompt files support YAML front-matter for metadata
        lines.append("---")
        lines.append(f'description: "{self.description}"')
        # VS Code Copilot prompt files always use mode: "agent" for agentic execution
        lines.append('mode: "agent"')
        # Map USCP execution modes to Copilot tool settings
        tools: list[str] = []
        allowed_tools = self._manifest.get("permissions", {}).get("tools", {}).get("allowed", [])
        for t in allowed_tools:
            # Map MCP tool names to Copilot tool identifiers
            copilot_tool = t.replace("mcp.", "").replace(".", "_")
            tools.append(copilot_tool)
        if tools:
            lines.append(f"tools: [{', '.join(tools)}]")
        lines.append("---")
        lines.append("")

        # Title
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"_{self.description}_")
        lines.append("")

        # Arguments
        arg_lines = self._arg_lines()
        if arg_lines:
            lines.append("## Arguments")
            lines.append("")
            lines.extend(arg_lines)
            lines.append("")

        # Workflow as the prompt body
        lines.append("## Steps")
        lines.append("")
        for step_line in self._workflow_lines():
            lines.append(step_line)
        lines.append("")

        # Output expectations
        output = self._manifest.get("output", {})
        sections = output.get("sections", [])
        if sections:
            lines.append("## Output Structure")
            lines.append("")
            lines.append("Your response must include the following sections:")
            lines.append("")
            for s in sections:
                lines.append(f"### {s}")
            lines.append("")

        # Safety
        perms = self._manifest.get("permissions", {})
        write_paths = perms.get("filesystem", {}).get("write", [])
        if not write_paths:
            lines.append(
                "> **Note**: This is a read-only command. Do not propose file changes."
            )
        else:
            write_list = ", ".join(f"`{p}`" for p in write_paths)
            lines.append(
                f"> **Note**: You may only write to: {write_list}. "
                "Require confirmation before writing."
            )
        lines.append("")

        return "\n".join(lines)
