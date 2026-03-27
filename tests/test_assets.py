"""Tests for mkdocs_claude_chat._internal.assets."""

from __future__ import annotations

from pathlib import Path

from mkdocs_claude_chat._internal.assets import copy_to_site, register


def test_register_appends_css() -> None:
    extra_css: list[str] = []
    register(extra_css, [])
    assert "assets/chat.css" in extra_css


def test_register_appends_js() -> None:
    extra_js: list[str] = []
    register([], extra_js)
    assert "assets/chat.js" in extra_js


def test_register_no_duplicates() -> None:
    extra_css: list[str] = []
    extra_js: list[str] = []
    register(extra_css, extra_js)
    register(extra_css, extra_js)
    assert extra_css.count("assets/chat.css") == 1
    assert extra_js.count("assets/chat.js") == 1


def test_copy_to_site_creates_files(tmp_path: Path) -> None:
    copy_to_site(str(tmp_path))
    assert (tmp_path / "assets" / "chat.css").exists()
    assert (tmp_path / "assets" / "chat.js").exists()


def test_copy_to_site_creates_dir(tmp_path: Path) -> None:
    site_dir = tmp_path / "site"
    copy_to_site(str(site_dir))
    assert (site_dir / "assets").is_dir()


def test_copy_to_site_content(tmp_path: Path) -> None:
    copy_to_site(str(tmp_path))
    assert (tmp_path / "assets" / "chat.css").stat().st_size > 0
    assert (tmp_path / "assets" / "chat.js").stat().st_size > 0
