"""Tests for the MkDocs plugin hooks."""

from __future__ import annotations

from pathlib import Path

import pytest
from mkdocs.config.defaults import MkDocsConfig

from mkdocs_ask_claude._internal.plugin import MkdocsAskClaudePlugin


def _make_config(tmp_path: Path, **plugin_opts: object) -> MkDocsConfig:
    """Build a minimal MkDocsConfig with the plugin enabled."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    conf = MkDocsConfig()
    conf.load_dict({
        "site_name": "Test",
        "site_url": "https://example.org/",
        "site_dir": str(tmp_path / "site"),
        "docs_dir": str(docs_dir),
        "plugins": {"ask-claude": plugin_opts},
    })
    errors, warnings = conf.validate()
    assert not errors, errors
    return conf


# --- on_config ---

def test_on_config_registers_assets(tmp_path: Path) -> None:
    conf = _make_config(tmp_path)
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    plugin.on_config(conf)
    assert "assets/chat.css" in conf["extra_css"]
    assert "assets/chat.js" in conf["extra_javascript"]


def test_on_config_derives_llmstxt_url(tmp_path: Path) -> None:
    conf = _make_config(tmp_path)
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    plugin.on_config(conf)
    assert plugin._llmstxt_url == "https://example.org/llms.txt"


def test_on_config_uses_explicit_llmstxt_url(tmp_path: Path) -> None:
    conf = _make_config(tmp_path, llmstxt_url="https://custom.example.com/llms.txt")
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    plugin.on_config(conf)
    assert plugin._llmstxt_url == "https://custom.example.com/llms.txt"


def test_on_config_disabled_returns_none(tmp_path: Path) -> None:
    conf = _make_config(tmp_path, enabled=False)
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    result = plugin.on_config(conf)
    assert result is None
    assert "assets/chat.css" not in conf["extra_css"]


# --- on_post_build ---

def test_on_post_build_copies_assets(tmp_path: Path) -> None:
    conf = _make_config(tmp_path)
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    plugin.on_config(conf)
    plugin.on_post_build(config=conf)
    assert (tmp_path / "site" / "assets" / "chat.css").exists()
    assert (tmp_path / "site" / "assets" / "chat.js").exists()


def test_on_post_build_disabled_no_copy(tmp_path: Path) -> None:
    conf = _make_config(tmp_path, enabled=False)
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    plugin.on_post_build(config=conf)
    assert not (tmp_path / "site" / "assets" / "chat.css").exists()


# --- on_page_context ---

def test_on_page_context_injects_config(tmp_path: Path) -> None:
    conf = _make_config(tmp_path)
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    plugin.on_config(conf)
    context: dict = {}
    plugin.on_page_context(context, page=object(), config=conf)  # type: ignore[arg-type]
    cfg = context["claude_chat_config"]
    assert "model" in cfg
    assert "chat_title" in cfg
    assert "position" in cfg
    assert "llmstxt_url" in cfg
    assert "system_prompt" in cfg


def test_on_page_context_disabled_returns_none(tmp_path: Path) -> None:
    conf = _make_config(tmp_path, enabled=False)
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    context: dict = {}
    result = plugin.on_page_context(context, page=object(), config=conf)  # type: ignore[arg-type]
    assert result is None
    assert "claude_chat_config" not in context


# --- on_post_page ---

_SAMPLE_HTML = "<html><body><p>Hello</p></body></html>"


def test_on_post_page_injects_script(tmp_path: Path) -> None:
    conf = _make_config(tmp_path)
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    plugin.on_config(conf)
    result = plugin.on_post_page(_SAMPLE_HTML, page=object(), config=conf)  # type: ignore[arg-type]
    assert result is not None
    assert "<script>window.__CLAUDE_CHAT_CONFIG__" in result
    assert "</body>" in result
    assert result.index("<script>window.__CLAUDE_CHAT_CONFIG__") < result.index("</body>")


def test_on_post_page_disabled_returns_none(tmp_path: Path) -> None:
    conf = _make_config(tmp_path, enabled=False)
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    result = plugin.on_post_page(_SAMPLE_HTML, page=object(), config=conf)  # type: ignore[arg-type]
    assert result is None


def test_on_post_page_config_values(tmp_path: Path) -> None:
    import json

    conf = _make_config(tmp_path, chat_title="My Docs Chat")
    plugin: MkdocsAskClaudePlugin = conf.plugins["ask-claude"]
    plugin.on_config(conf)
    result = plugin.on_post_page(_SAMPLE_HTML, page=object(), config=conf)  # type: ignore[arg-type]
    assert result is not None
    # Extract the JSON from the script tag
    start = result.index("__CLAUDE_CHAT_CONFIG__ = ") + len("__CLAUDE_CHAT_CONFIG__ = ")
    end = result.index(";", start)
    cfg = json.loads(result[start:end])
    assert "backendUrl" in cfg
    assert "llmstxtUrl" in cfg
    assert cfg["chatTitle"] == "My Docs Chat"
    assert "position" in cfg
