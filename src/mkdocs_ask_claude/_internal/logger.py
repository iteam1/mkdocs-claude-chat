"""Logging utilities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logging import Logger


class _PluginLogger(logging.LoggerAdapter):
    """Logger adapter that prefixes every message with the plugin name.

    Args:
        prefix: The prefix string inserted before every log message.
        logger: The underlying :class:`logging.Logger` instance.
    """

    def __init__(self, prefix: str, logger: Logger) -> None:
        super().__init__(logger, {})
        self._prefix = prefix

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Prepend the plugin prefix to every log message.

        Args:
            msg: The original log message.
            kwargs: Keyword arguments passed to the logging call.

        Returns:
            A tuple of the prefixed message and the unchanged kwargs.
        """
        return f"{self._prefix}: {msg}", kwargs


def get_logger(name: str) -> _PluginLogger:
    """Return a logger prefixed with ``ask-claude:`` for the given module name.

    Writes to the ``mkdocs.plugins.ask-claude.<module>`` namespace so that
    MkDocs' existing log level and handler configuration applies automatically.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A :class:`_PluginLogger` adapter ready for use.

    Example:
        .. code-block:: python

            _logger = get_logger(__name__)
            _logger.debug("plugin initialised")
    """
    module = name.split(".")[-1] if name else "unknown"
    logger = logging.getLogger(f"mkdocs.plugins.ask-claude.{module}")
    return _PluginLogger("ask-claude", logger)
