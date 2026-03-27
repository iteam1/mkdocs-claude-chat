# Tasks: Plugin Hooks

**Input**: Design documents from `/specs/003-plugin-hooks/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

- [ ] T001 Verify `src/mkdocs_claude_chat/_internal/plugin.py` exists as a stub with `MkdocsClaudeChatPlugin(BasePlugin[_PluginConfig])`
- [ ] T002 Verify `logger.py` and `assets.py` are implemented (features 001 and 002)

---

## Phase 2: Foundational

No blocking prerequisites beyond 001/002. Proceed to user stories.

---

## Phase 3: User Story 1 — Assets injected into every built page (Priority: P1) 🎯 MVP

**Goal**: `on_config` registers assets and resolves `llmstxt_url`; `on_post_build` copies files to `site_dir`.

**Independent Test**: Run `mkdocs build`; verify `site/assets/chat.css` and `site/assets/chat.js` exist.

- [ ] T003 [US1] Add module-level imports and `_logger = get_logger(__name__)` to `src/mkdocs_claude_chat/_internal/plugin.py`
- [ ] T004 [US1] Declare `_llmstxt_url: str` as class-level type hint on `MkdocsClaudeChatPlugin` in `src/mkdocs_claude_chat/_internal/plugin.py`
- [ ] T005 [US1] Implement `on_config(self, config, **kwargs)` — short-circuit on disabled, resolve `llmstxt_url`, call `assets.register()` in `src/mkdocs_claude_chat/_internal/plugin.py`
- [ ] T006 [US1] Implement `on_post_build(self, *, config, **kwargs)` — short-circuit on disabled, call `assets.copy_to_site()` in `src/mkdocs_claude_chat/_internal/plugin.py`

**Checkpoint**: `on_config` + `on_post_build` complete — US1 done.

---

## Phase 4: User Story 2 — Chat config available on every page (Priority: P2)

**Goal**: `on_page_context` injects `claude_chat_config` dict into every page's template context.

**Independent Test**: After `on_page_context` runs, assert `context["claude_chat_config"]` contains all five expected keys.

- [ ] T007 [US2] Implement `on_page_context(self, context, /, *, page, config, **kwargs)` — short-circuit on disabled, inject `claude_chat_config` dict in `src/mkdocs_claude_chat/_internal/plugin.py`
- [ ] T008 [US2] Add Google-style docstrings to all three hooks in `src/mkdocs_claude_chat/_internal/plugin.py`

**Checkpoint**: All three hooks complete — US1 and US2 done.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T009 [P] Write unit tests for all three hooks in `tests/test_plugin.py` using real `MkDocsConfig` objects (no mocks for MkDocs internals), covering: assets registered, llmstxt_url derived/explicit, disabled short-circuit, files copied, context injected

---

## Dependencies & Execution Order

- T001, T002 — parallel setup checks
- T003 → T004 → T005 → T006 — sequential (same file)
- T007 → T008 — sequential (same file, depends on T003–T006 for imports)
- T009 — after T008

---

## Implementation Strategy

### MVP (US1 + US2)

1. T001, T002 — verify prerequisites
2. T003 → T004 → T005 → T006 — `on_config` + `on_post_build`
3. T007 → T008 — `on_page_context` + docstrings
4. T009 — tests

**Total tasks**: 9
**MVP tasks**: 8 (T001–T008)
