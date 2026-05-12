"""Base adapter — abstract interface all host adapters must implement."""

from __future__ import annotations

import abc
import pathlib
from typing import Any


class BaseAdapter(abc.ABC):
    """Abstract base class for USCP host adapters.

    Each adapter translates a universal command manifest into the
    tool-specific format understood by one agentic coding environment.
    """

    #: Human-readable name of the target tool.
    target_name: str = ""

    def __init__(self, manifest: dict[str, Any]) -> None:
        self._manifest = manifest

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def render(self) -> str:
        """Render the manifest to the tool-specific format as a string."""

    @abc.abstractmethod
    def output_filename(self) -> str:
        """Return the recommended output filename (without directory prefix)."""

    # ------------------------------------------------------------------
    # Helpers available to subclasses
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return self._manifest.get("name", "unknown")

    @property
    def title(self) -> str:
        return self._manifest.get("title", self.name)

    @property
    def description(self) -> str:
        return self._manifest.get("description", "")

    @property
    def arguments(self) -> dict[str, Any]:
        return self._manifest.get("arguments", {})

    @property
    def workflow_steps(self) -> list[dict[str, Any]]:
        return self._manifest.get("workflow", {}).get("steps", [])

    @property
    def examples(self) -> list[str]:
        return self._manifest.get("examples", [])

    def _arg_lines(self) -> list[str]:
        """Return argument descriptions as markdown bullet points."""
        props = self.arguments.get("properties", {})
        required = self.arguments.get("required", [])
        lines = []
        for arg_name, arg_def in props.items():
            req = " *(required)*" if arg_name in required else ""
            desc = arg_def.get("description", "")
            arg_type = arg_def.get("type", "string")
            enum_vals = arg_def.get("enum")
            enum_str = f" Allowed: `{'`, `'.join(str(v) for v in enum_vals)}`." if enum_vals else ""
            default = arg_def.get("default")
            default_str = f" Default: `{default}`." if default is not None else ""
            lines.append(f"- `--{arg_name}` (`{arg_type}`){req}: {desc}{enum_str}{default_str}")
        return lines

    def _workflow_lines(self) -> list[str]:
        """Return workflow steps as numbered markdown items."""
        lines = []
        for i, step in enumerate(self.workflow_steps, 1):
            instr = step.get("instruction", "").strip()
            lines.append(f"{i}. **{step['id']}**: {instr}")
        return lines

    def write(self, output_dir: str | pathlib.Path) -> pathlib.Path:
        """Render the manifest and write it to *output_dir*.

        Returns the path of the written file.
        """
        out = pathlib.Path(output_dir) / self.output_filename()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.render(), encoding="utf-8")
        return out
