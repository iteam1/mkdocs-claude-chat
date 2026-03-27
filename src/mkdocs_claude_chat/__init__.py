"""mkdocs-claude-chat package.

MkDocs plugin to add a Claude-powered chatbot to your documentation site.
"""

from __future__ import annotations

from mkdocs_claude_chat._internal.plugin import MkdocsClaudeChatPlugin

__all__: list[str] = [
    "MkdocsClaudeChatPlugin",
]
