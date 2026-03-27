# Tasks: Assets Injection

**Input**: Design documents from `/specs/002-assets-injection/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

- [x] T001 Verify `src/mkdocs_claude_chat/_internal/assets.py` exists as a stub
- [x] T002 Verify `src/mkdocs_claude_chat/assets/chat.css` and `chat.js` exist as source files

---

## Phase 2: Foundational

No blocking prerequisites — `assets.py` depends only on Python stdlib. Proceed to user stories.

---

## Phase 3: User Story 1 — CSS and JS are available on every built page (Priority: P1) 🎯 MVP

**Goal**: `copy_to_site(site_dir)` copies bundled assets into the built site's `assets/` directory.

**Independent Test**: Call `copy_to_site(tmp_path)` and verify `tmp_path/assets/chat.css` and `tmp_path/assets/chat.js` exist and are non-empty.

- [x] T003 [US1] Define `ASSETS_DIR = Path(__file__).parent.parent / "assets"` constant in `src/mkdocs_claude_chat/_internal/assets.py`
- [x] T004 [US1] Implement `copy_to_site(site_dir: str) -> None` that creates `site_dir/assets/` and copies `chat.css` and `chat.js` in `src/mkdocs_claude_chat/_internal/assets.py`
- [x] T005 [US1] Add `from __future__ import annotations`, type hints, and Google-style docstrings in `src/mkdocs_claude_chat/_internal/assets.py`

**Checkpoint**: `copy_to_site` works independently — US1 complete.

---

## Phase 4: User Story 2 — Assets registered with MkDocs at config time (Priority: P2)

**Goal**: `register(extra_css, extra_javascript)` appends the chat asset paths to MkDocs config lists.

**Independent Test**: Call `register([], [])` and assert both lists contain the expected path strings.

- [x] T006 [US2] Implement `register(extra_css: list, extra_javascript: list) -> None` that appends `"assets/chat.css"` and `"assets/chat.js"` in `src/mkdocs_claude_chat/_internal/assets.py`

**Checkpoint**: Both functions complete — US1 and US2 done.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T007 [P] Write unit tests for `register` and `copy_to_site` in `tests/test_assets.py` covering: CSS appended, JS appended, no duplicates on double call, files created, dir auto-created, files non-empty

---

## Dependencies & Execution Order

- T001, T002 — parallel setup verification
- T003 → T004 → T005 — sequential (same file)
- T006 — can run after T003 (same file, no dependency on T004/T005)
- T007 — after T006

---

## Implementation Strategy

### MVP (US1 + US2)

1. T001, T002 — verify stubs
2. T003 → T004 → T005 — implement `copy_to_site`
3. T006 — implement `register`
4. T007 — tests

**Total tasks**: 7
**MVP tasks**: 6 (T001–T006)
