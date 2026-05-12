"""Adapters package — tool-specific command compilers."""

from uscp.adapters.base import BaseAdapter
from uscp.adapters.claude_code import ClaudeCodeAdapter
from uscp.adapters.codex import CodexAdapter
from uscp.adapters.cursor import CursorAdapter
from uscp.adapters.vscode_copilot import VSCodeCopilotAdapter

ADAPTERS: dict[str, type[BaseAdapter]] = {
    "claude-code": ClaudeCodeAdapter,
    "codex": CodexAdapter,
    "vscode-copilot": VSCodeCopilotAdapter,
    "cursor": CursorAdapter,
}

__all__ = [
    "BaseAdapter",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "CursorAdapter",
    "VSCodeCopilotAdapter",
    "ADAPTERS",
]
