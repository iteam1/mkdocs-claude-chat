# Implementation Plan: Logger Adapter

**Branch**: `001-logger-adapter` | **Date**: 2026-03-27 | **Spec**: [spec.md](spec.md)

## Summary

Implement `src/mkdocs_claude_chat/_internal/logger.py` — a thin `LoggerAdapter` subclass that prefixes every log message with `claude-chat:` and routes records to the `mkdocs.plugins.claude-chat.<module>` namespace. All other `_internal` modules will call `get_logger(__name__)` at module level.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: stdlib `logging` only — no new packages
**Storage**: N/A
**Testing**: pytest
**Target Platform**: Any (library module, runs inside MkDocs process)
**Project Type**: MkDocs plugin (library)
**Performance Goals**: N/A — logging is not a bottleneck
**Constraints**: Zero external dependencies; must not interfere with MkDocs log level config

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule (Constitution §) | Status | Notes |
|---|---|---|
| §II — `_internal/` only | ✅ | File lives in `_internal/logger.py` |
| §VII — `from __future__ import annotations` | ✅ | Required in all modules |
| §VII — Full type annotations on public functions | ✅ | `get_logger` will be annotated |
| §VIII — Prefix `claude-chat:`, namespace `mkdocs.plugins.*` | ✅ | Exact pattern from constitution |
| §X — Google docstring convention | ✅ | Applied to all public items |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-logger-adapter/
├── plan.md              ← this file
├── research.md          ← Phase 0 (N/A — no unknowns)
├── data-model.md        ← Phase 1 (N/A — no data entities)
└── tasks.md             ← Phase 2 (/speckit.tasks)
```

### Source Code

```text
src/mkdocs_claude_chat/_internal/
└── logger.py            ← new implementation

tests/
└── test_logger.py       ← new unit tests
```

---

## Phase 0: Research

No unknowns. Constitution §VIII prescribes the exact implementation pattern. No external research needed.

See [research.md](research.md) for decisions recorded.

---

## Phase 1: Design

### Interface contract

`logger.py` is a purely internal module. Its public surface is one function:

```
get_logger(name: str) -> _PluginLogger
```

- `name` — typically `__name__` of the calling module (e.g. `mkdocs_claude_chat._internal.plugin`)
- Returns a `_PluginLogger` (subclass of `logging.LoggerAdapter`) that:
  - Prefixes every message with `claude-chat: `
  - Writes to logger named `mkdocs.plugins.claude-chat.<last segment of name>`

### `_PluginLogger` design

```
_PluginLogger(logging.LoggerAdapter)
  __init__(prefix: str, logger: Logger) -> None
  process(msg: str, kwargs: dict) -> tuple[str, dict]
    → returns (f"claude-chat: {msg}", kwargs)
```

No state beyond `prefix`. All log level methods (`debug`, `info`, `warning`, `error`, `critical`) are inherited from `LoggerAdapter` unchanged.

### Usage pattern (all `_internal` modules)

```python
from mkdocs_claude_chat._internal.logger import get_logger
_logger = get_logger(__name__)

# later:
_logger.debug("registered assets")
_logger.warning("llmstxt_url not set")
```

### Test plan

| Test | What it checks |
|---|---|
| `test_get_logger_returns_adapter` | Return type is `_PluginLogger` |
| `test_prefix_applied` | Emitted record message starts with `claude-chat: ` |
| `test_namespace` | Logger name matches `mkdocs.plugins.claude-chat.<module>` |
| `test_all_levels` | debug/info/warning/error/critical all work without exceptions |
| `test_empty_name` | No exception raised when `name=""` |
