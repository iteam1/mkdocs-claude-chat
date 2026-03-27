"""Plugin configuration schema."""

from __future__ import annotations

import mkdocs.config.config_options as mkconf
from mkdocs.config.base import Config


class _PluginConfig(Config):
    """Configuration options for mkdocs-claude-chat."""

    enabled = mkconf.Type(bool, default=True)
    model = mkconf.Type(str, default="claude-sonnet-4-6")
    system_prompt = mkconf.Optional(mkconf.Type(str))
    llmstxt_url = mkconf.Optional(mkconf.Type(str))  # auto-derived from site_url if omitted
    chat_title = mkconf.Type(str, default="Ask Claude")
    position = mkconf.Type(str, default="bottom-right")
    # Backend server
    backend_port = mkconf.Type(int, default=8001)
    # Session management
    session_ttl = mkconf.Type(int, default=7200)   # seconds of inactivity before a session is evicted
    max_sessions = mkconf.Type(int, default=10)    # max simultaneous live Claude processes
