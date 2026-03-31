"""Asset injection helpers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

ASSETS_DIR: Path = Path(__file__).parent.parent / "assets"


def register(extra_css: list[str], extra_javascript: list[str]) -> None:
    """Append the plugin's CSS and JS paths to MkDocs config lists.

    ``chat-config.js`` is registered before ``chat.js`` so the config
    variable is defined when the widget script runs.
    """
    if "assets/chat.css" not in extra_css:
        extra_css.append("assets/chat.css")
    if "assets/chat-config.js" not in extra_javascript:
        extra_javascript.append("assets/chat-config.js")
    if "assets/chat.js" not in extra_javascript:
        extra_javascript.append("assets/chat.js")


def copy_to_site(site_dir: str) -> None:
    """Copy bundled CSS and JS into the built site's assets directory."""
    dest = Path(site_dir) / "assets"
    dest.mkdir(parents=True, exist_ok=True)
    for asset in ("chat.css", "chat.js"):
        shutil.copy2(ASSETS_DIR / asset, dest / asset)


def write_config(site_dir: str, cfg: dict[str, Any]) -> None:
    """Write ``chat-config.js`` so every page (including 404) gets the config."""
    dest = Path(site_dir) / "assets" / "chat-config.js"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        f"window.__CLAUDE_CHAT_CONFIG__ = {json.dumps(cfg)};\n",
        encoding="utf-8",
    )
