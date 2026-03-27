"""Asset injection helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

ASSETS_DIR: Path = Path(__file__).parent.parent / "assets"


def register(extra_css: list[str], extra_javascript: list[str]) -> None:
    """Append the plugin's CSS and JS paths to MkDocs config lists.

    Mutates ``extra_css`` and ``extra_javascript`` in place. Safe to call
    multiple times — duplicate entries are not added.

    Args:
        extra_css: The ``config["extra_css"]`` list from MkDocs.
        extra_javascript: The ``config["extra_javascript"]`` list from MkDocs.
    """
    if "assets/chat.css" not in extra_css:
        extra_css.append("assets/chat.css")
    if "assets/chat.js" not in extra_javascript:
        extra_javascript.append("assets/chat.js")


def copy_to_site(site_dir: str) -> None:
    """Copy bundled CSS and JS into the built site's assets directory.

    Creates ``<site_dir>/assets/`` if it does not already exist, then copies
    ``chat.css`` and ``chat.js`` from the package's bundled ``assets/``
    directory.

    Args:
        site_dir: Absolute path to the MkDocs ``site_dir``.
    """
    dest = Path(site_dir) / "assets"
    dest.mkdir(parents=True, exist_ok=True)
    for asset in ("chat.css", "chat.js"):
        shutil.copy2(ASSETS_DIR / asset, dest / asset)
