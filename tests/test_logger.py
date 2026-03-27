"""Tests for mkdocs_ask_claude._internal.logger."""

from __future__ import annotations

import logging

import pytest

from mkdocs_ask_claude._internal.logger import _PluginLogger, get_logger


def test_get_logger_returns_adapter() -> None:
    assert isinstance(get_logger("mkdocs_ask_claude._internal.plugin"), _PluginLogger)


def test_namespace() -> None:
    l = get_logger("mkdocs_ask_claude._internal.plugin")
    assert l.logger.name == "mkdocs.plugins.ask-claude.plugin"


def test_namespace_uses_last_segment() -> None:
    l = get_logger("mkdocs_ask_claude._internal.assets")
    assert l.logger.name == "mkdocs.plugins.ask-claude.assets"


def test_prefix_applied(caplog: pytest.LogCaptureFixture) -> None:
    l = get_logger("mkdocs_ask_claude._internal.plugin")
    with caplog.at_level(logging.INFO, logger="mkdocs.plugins.ask-claude.plugin"):
        l.info("hello world")
    assert any("ask-claude: hello world" in r.message for r in caplog.records)


@pytest.mark.parametrize("level", ["debug", "info", "warning", "error", "critical"])
def test_all_levels(level: str) -> None:
    l = get_logger("mkdocs_ask_claude._internal.plugin")
    getattr(l, level)("msg")  # must not raise


def test_empty_name_no_exception() -> None:
    l = get_logger("")
    assert isinstance(l, _PluginLogger)
    l.info("edge case")  # must not raise
