"""Main MkDocs plugin implementation."""

from __future__ import annotations

from mkdocs.plugins import BasePlugin
from mkdocs_claude_chat._internal.config import _PluginConfig


class MkdocsClaudeChatPlugin(BasePlugin[_PluginConfig]):
    """MkDocs plugin that injects a Claude-powered chatbot widget into every page."""
