"""mkdocs-ask-claude package.

MkDocs plugin to add a Claude-powered chatbot to your documentation site.
"""

from __future__ import annotations

from mkdocs_ask_claude._internal.plugin import MkdocsAskClaudePlugin

__all__: list[str] = [
    "MkdocsAskClaudePlugin",
]
