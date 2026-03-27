"""Main MkDocs plugin implementation."""

from __future__ import annotations

import json
import threading
from typing import TYPE_CHECKING

from mkdocs.plugins import BasePlugin

from mkdocs_claude_chat._internal import assets, server
from mkdocs_claude_chat._internal.config import _PluginConfig
from mkdocs_claude_chat._internal.logger import get_logger

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.pages import Page

_logger = get_logger(__name__)


class MkdocsClaudeChatPlugin(BasePlugin[_PluginConfig]):
    """MkDocs plugin that injects a Claude-powered chatbot widget into every page."""

    _llmstxt_url: str
    _is_serving: bool = False

    def on_config(self, config: MkDocsConfig, **kwargs: object) -> MkDocsConfig | None:
        """Register chat assets and resolve the llms.txt URL.

        Called once at the start of every MkDocs build or serve cycle. Appends
        the plugin's CSS and JS to the MkDocs extra-assets lists and stores the
        resolved ``llmstxt_url`` for later use in :meth:`on_page_context`.

        Args:
            config: The global MkDocs configuration object.
            **kwargs: Accepted for forward-compatibility with future MkDocs versions.

        Returns:
            The (mutated) config object, or ``None`` when the plugin is disabled.
        """
        if not self.config.enabled:
            return None

        if self.config.llmstxt_url:
            self._llmstxt_url = self.config.llmstxt_url.rstrip("/")
        elif self._is_serving:
            # During `mkdocs serve`, use the local dev server address.
            # Preserve the path component from site_url (e.g. /mkdocs-claude-chat/)
            # because MkDocs dev server mirrors that path structure.
            from urllib.parse import urlparse  # noqa: PLC0415
            dev_addr = config.get("dev_addr") or "127.0.0.1:8000"
            site_url = (config.get("site_url") or "").rstrip("/")
            site_path = urlparse(site_url).path.rstrip("/") if site_url else ""
            self._llmstxt_url = f"http://{dev_addr}{site_path}/llms.txt"
        else:
            site_url = (config.get("site_url") or "").rstrip("/")
            self._llmstxt_url = f"{site_url}/llms.txt" if site_url else ""

        assets.register(config["extra_css"], config["extra_javascript"])
        _logger.debug("registered chat assets, llmstxt_url=%s", self._llmstxt_url)
        return config

    def on_post_build(self, *, config: MkDocsConfig, **kwargs: object) -> None:
        """Copy bundled chat assets and tell the server where the site lives.

        Called once after all pages have been written. Copies ``chat.css`` and
        ``chat.js`` from the package into ``<site_dir>/assets/``. When serving,
        also tells the chat backend where to find ``llms-full.txt`` / ``llms.txt``
        so it can read them directly from disk — no HTTP fetch required.

        Args:
            config: The global MkDocs configuration object.
            **kwargs: Accepted for forward-compatibility with future MkDocs versions.
        """
        if not self.config.enabled:
            return
        assets.copy_to_site(config["site_dir"])
        _logger.debug("copied chat assets to site_dir")
        if self._is_serving:
            server.configure(config["site_dir"], self._llmstxt_url)

    def on_page_context(
        self,
        context: dict,
        /,
        *,
        page: Page,
        config: MkDocsConfig,
        **kwargs: object,
    ) -> dict | None:
        """Inject the chat widget configuration into each page's template context.

        Adds ``claude_chat_config`` to the Jinja2 context so themes can render
        ``window.__CLAUDE_CHAT_CONFIG__`` into the page HTML.

        Args:
            context: The Jinja2 template context for the current page.
            page: The MkDocs ``Page`` object being rendered.
            config: The global MkDocs configuration object.
            **kwargs: Accepted for forward-compatibility with future MkDocs versions.

        Returns:
            The (mutated) context dict, or ``None`` when the plugin is disabled.
        """
        if not self.config.enabled:
            return None

        context["claude_chat_config"] = {
            "model": self.config.model,
            "chat_title": self.config.chat_title,
            "position": self.config.position,
            "llmstxt_url": self._llmstxt_url,
            "system_prompt": self.config.system_prompt or "",
        }
        return context

    def on_startup(self, *, command: str, dirty: bool, **kwargs: object) -> None:
        """Start the chat backend when ``mkdocs serve`` is invoked.

        Args:
            command: The MkDocs command being run (``"serve"``, ``"build"``, etc.).
            dirty: Whether a dirty build was requested.
            **kwargs: Accepted for forward-compatibility.
        """
        if command != "serve" or not self.config.enabled:
            return
        self._is_serving = True
        _logger.info("starting chat backend on http://localhost:8001")

        def _run() -> None:
            try:
                server.run()
            except Exception as exc:  # noqa: BLE001
                _logger.error("chat backend crashed: %s", exc)

        t = threading.Thread(target=_run, daemon=True)
        t.start()


    def on_post_page(
        self,
        output: str,
        *,
        page: Page,
        config: MkDocsConfig,
        **kwargs: object,
    ) -> str | None:
        """Inject the chat widget config into each page's HTML output.

        Inserts a ``<script>window.__CLAUDE_CHAT_CONFIG__ = {...};</script>``
        block immediately before the closing ``</body>`` tag so the widget
        can read its settings without requiring any theme template override.

        Args:
            output: The rendered HTML string for the current page.
            page: The MkDocs ``Page`` object being rendered.
            config: The global MkDocs configuration object.
            **kwargs: Accepted for forward-compatibility with future MkDocs versions.

        Returns:
            The modified HTML string, or ``None`` when the plugin is disabled.
        """
        if not self.config.enabled:
            return None

        cfg = {
            "backendUrl": "http://localhost:8001",
            "llmstxtUrl": self._llmstxt_url,
            "chatTitle": self.config.chat_title,
            "position": self.config.position,
            "systemPrompt": self.config.system_prompt or "",
        }
        script = f"<script>window.__CLAUDE_CHAT_CONFIG__ = {json.dumps(cfg)};</script>"
        return output.replace("</body>", f"{script}\n</body>", 1)
