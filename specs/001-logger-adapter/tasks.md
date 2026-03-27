# Tasks: Logger Adapter

**Input**: Design documents from `/specs/001-logger-adapter/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

**Purpose**: Confirm the target file exists and is ready for implementation

- [ ] T001 Verify `src/mkdocs_claude_chat/_internal/logger.py` exists as a stub (docstring + `from __future__ import annotations` only)

---

## Phase 2: Foundational

**Purpose**: No blocking prerequisites — `logger.py` depends only on Python stdlib. Skip to Phase 3.

---

## Phase 3: User Story 1 — Plugin emits identifiable log messages (Priority: P1) 🎯 MVP

**Goal**: `logger.py` is fully implemented; every `_internal` module can call `get_logger(__name__)` and emit prefixed log messages.

**Independent Test**: Run `python -c "from mkdocs_claude_chat._internal.logger import get_logger; l = get_logger('mkdocs_claude_chat._internal.plugin'); l.info('test')"` and confirm output contains `claude-chat: test`.

### Implementation

- [ ] T002 [US1] Implement `_PluginLogger(logging.LoggerAdapter)` with `process()` method that prepends `claude-chat: ` to every message in `src/mkdocs_claude_chat/_internal/logger.py`
- [ ] T003 [US1] Implement `get_logger(name: str) -> _PluginLogger` that creates a logger under `mkdocs.plugins.claude-chat.<last segment of name>` in `src/mkdocs_claude_chat/_internal/logger.py`
- [ ] T004 [US1] Add `from __future__ import annotations`, type hints, and Google-style docstrings to all public items in `src/mkdocs_claude_chat/_internal/logger.py`

**Checkpoint**: `get_logger(__name__)` works and produces prefixed output — US1 complete.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [ ] T005 [P] Write unit tests for `_PluginLogger` and `get_logger` in `tests/test_logger.py` covering: return type, prefix, namespace, all log levels, empty name edge case
- [ ] T006 [P] Update `constitution.md` §V to remove `tools.py` reference (already outdated — align with CLAUDE.md decision)

---

## Dependencies & Execution Order

- **T001** → **T002** → **T003** → **T004** (sequential, same file)
- **T005**, **T006** can run in parallel after T004

---

## Parallel Opportunities

```bash
# After T004 completes, launch in parallel:
Task T005: "Write unit tests in tests/test_logger.py"
Task T006: "Update constitution.md §V"
```

---

## Implementation Strategy

### MVP (US1 only)

1. T001 — verify stub
2. T002 → T003 → T004 — implement logger
3. Validate with manual smoke test
4. T005 — add tests

**Total tasks**: 6
**MVP tasks**: 4 (T001–T004)
