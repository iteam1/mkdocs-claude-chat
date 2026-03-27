"""Plugin configuration schema."""

from __future__ import annotations

import mkdocs.config.config_options as mkconf
from mkdocs.config.base import Config


class _PluginConfig(Config):
    """Configuration options for mkdocs-claude-chat."""

    enabled = mkconf.Type(bool, default=True)
    model = mkconf.Type(str, default="claude-sonnet-4-6")
    system_prompt = mkconf.Optional(mkconf.Type(str))
    llmstxt_url = mkconf.Optional(mkconf.Type(str))
    chat_title = mkconf.Type(str, default="Ask Claude")
    position = mkconf.Type(str, default="bottom-right")
