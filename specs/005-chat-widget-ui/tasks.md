# Tasks: Chat Widget UI

**Input**: Design documents from `/specs/005-chat-widget-ui/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, contracts/widget-contract.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

- [x] T001 Verify `src/mkdocs_claude_chat/assets/chat.js` and `chat.css` exist (create empty stubs if missing)

---

## Phase 2: Foundational

**Purpose**: Config injection hook in `plugin.py` — required by all user stories (widget reads `window.__CLAUDE_CHAT_CONFIG__`).

- [x] T002 Add `import json` to `src/mkdocs_claude_chat/_internal/plugin.py` (if not already present)
- [x] T003 Implement `on_post_page(self, output, *, page, config, **kwargs)` in `src/mkdocs_claude_chat/_internal/plugin.py` — build the config dict (`backendUrl`, `llmstxtUrl`, `chatTitle`, `position`), serialize to JSON, inject `<script>window.__CLAUDE_CHAT_CONFIG__ = {...};</script>` before `</body>`, return modified HTML; short-circuit when `self.config.enabled` is False
- [x] T004 Add three tests to `tests/test_plugin.py` — `test_on_post_page_injects_script`, `test_on_post_page_disabled`, `test_on_post_page_config_values` — verifying the script tag is present, absent when disabled, and contains the correct JSON fields

**Checkpoint**: Config is available to the widget on every page. Run `pytest tests/test_plugin.py` — all pass.

---

## Phase 3: User Story 1 — Open & Close the Chat Panel (Priority: P1) 🎯 MVP

**Goal**: A circular floating button appears on every page; clicking it opens/closes a right-side chat panel.

**Independent Test**: Open any MkDocs page, see the circle button in the bottom-right corner. Click it — the chat panel slides in from the right. Click again (or the × button) — the panel closes.

- [x] T005 [US1] Write CSS for `#claude-chat-btn` (56 px circle, fixed position, bottom-right default, `z-index: 9999`, box-shadow, hover effect) in `src/mkdocs_claude_chat/assets/chat.css`
- [x] T006 [US1] Write CSS for `#claude-chat-panel` (fixed right-side panel, full height, 360 px wide, hidden via `transform: translateX(100%)`, `.open` class applies `translateX(0)`, `transition: transform 0.25s ease`, `z-index: 9998`) in `src/mkdocs_claude_chat/assets/chat.css`
- [x] T007 [US1] Write CSS for panel interior layout (`.cc-header` with title + close button, `.cc-messages` flex-grow + overflow-y scroll, `.cc-input-row` flex row with input + send button, `.cc-bubble-user` and `.cc-bubble-assistant` chat bubbles) in `src/mkdocs_claude_chat/assets/chat.css`
- [x] T008 [US1] In `chat.js`: read `window.__CLAUDE_CHAT_CONFIG__` into module-level `cfg`; implement `createButton()` that builds and returns `#claude-chat-btn` DOM element in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T009 [US1] In `chat.js`: implement `createPanel()` that builds and returns `#claude-chat-panel` DOM with header (title from `cfg.chatTitle`, × close button), `.cc-messages` area, and `.cc-input-row` (text input + Send button) in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T010 [US1] In `chat.js`: implement `togglePanel()` that flips `panelOpen` state and adds/removes `.open` class on the panel element in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T011 [US1] In `chat.js`: implement `init()` that appends button and panel to `document.body`, wires click on button and × button to `togglePanel()`, and runs on `DOMContentLoaded` in `src/mkdocs_claude_chat/assets/chat.js`

**Checkpoint**: US1 complete. Reload the MkDocs site — button visible, panel opens/closes.

---

## Phase 4: User Story 2 — Ask a Question, Get a Streamed Answer (Priority: P1)

**Goal**: Typing a question and pressing Enter/Send streams a Claude answer into the chat panel token-by-token.

**Independent Test**: With the panel open, type "What is this documentation about?" and press Enter. A loading indicator appears, text streams in progressively, and the input re-enables when done.

- [x] T012 [US2] In `chat.js`: implement `appendMessage(role, text)` that creates a `.cc-bubble-user` or `.cc-bubble-assistant` div, appends it to `.cc-messages`, and scrolls the messages area to the bottom in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T013 [US2] In `chat.js`: implement `appendChunk(text)` that appends `text` to the last `.cc-bubble-assistant` element (creating one if none exists) and scrolls to bottom in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T014 [US2] In `chat.js`: implement `streamResponse(question)` as an async generator using `fetch` POST to `${cfg.backendUrl}/chat` with body `{question, llmstxt_url: cfg.llmstxtUrl}`, reads `ReadableStream` via `getReader()`, decodes with `TextDecoder`, buffers incomplete lines, yields each SSE `data:` payload string in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T015 [US2] In `chat.js`: implement `sendMessage()` that reads the input value, returns early if blank, appends the user bubble, disables the input + Send button, shows a loading indicator, iterates `streamResponse`, routes `{"text":...}` chunks to `appendChunk`, routes `{"error":...}` to an error bubble, handles `[DONE]` by removing the loading indicator and re-enabling the input in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T016 [US2] In `chat.js`: wire the Send button click and input `keydown` (Enter key, no shift) to `sendMessage()` inside `init()` in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T017 [US2] Write CSS for loading indicator (`.cc-loading` animated ellipsis or spinner), error bubble (`.cc-bubble-error` in red/warning color), and disabled input state in `src/mkdocs_claude_chat/assets/chat.css`

**Checkpoint**: US2 complete. Ask a question — see streamed Claude answer. Ask another — previous history preserved.

---

## Phase 5: User Story 3 — Drag the Button to Any Position (Priority: P2)

**Goal**: The circle button can be clicked-and-dragged to any position on screen; it stays there for the session and the chat still opens from the new position.

**Independent Test**: Drag the button from the bottom-right corner to the top-left area. Release. Button stays put. Click it — the panel opens correctly.

- [x] T018 [US3] In `chat.js`: add module-level drag state variables (`buttonX`, `buttonY`, `isDragging`, `dragStartX`, `dragStartY`, `dragMoved`) initialized to the bottom-right default position in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T019 [US3] In `chat.js`: implement `clampPosition(x, y)` that clamps the button center to `[28, window.innerWidth - 28]` × `[28, window.innerHeight - 28]` (28 = half of 56 px button) in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T020 [US3] In `chat.js`: implement `onPointerDown(e)` — record `dragStartX/Y`, set `isDragging = true`, call `btn.setPointerCapture(e.pointerId)` in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T021 [US3] In `chat.js`: implement `onPointerMove(e)` — if `isDragging`, compute new position, clamp it, apply `left/top` style to button, set `dragMoved = Math.hypot(dx,dy) >= 5` in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T022 [US3] In `chat.js`: implement `onPointerUp(e)` — if `!dragMoved` call `togglePanel()`, reset all drag state in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T023 [US3] In `chat.js`: wire `pointerdown`, `pointermove`, `pointerup` events on the button to the handlers above inside `init()`; remove the simple `click` listener (replaced by `onPointerUp` tap detection) in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T024 [US3] Write CSS for `cursor: grab` on `#claude-chat-btn` and `cursor: grabbing` when `.dragging` class is present; add `.dragging` class in `onPointerDown`, remove in `onPointerUp` in `src/mkdocs_claude_chat/assets/chat.css`

**Checkpoint**: US3 complete. All three user stories working. Drag button, ask question, close panel.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T025 [P] Add `@media (max-width: 480px)` rule to `#claude-chat-panel` making it `width: 100vw` in `src/mkdocs_claude_chat/assets/chat.css`
- [x] T026 [P] Add error handling in `sendMessage()` for network failure (catch on `fetch`) — display an error bubble and re-enable input in `src/mkdocs_claude_chat/assets/chat.js`
- [x] T027 [P] Add CSS custom properties (`--cc-primary`, `--cc-bg`, `--cc-text`, `--cc-radius`) at `:root` level so the widget is theme-customizable in `src/mkdocs_claude_chat/assets/chat.css`
- [x] T028 Update `CLAUDE.md` Active Technologies section to include the JS/CSS widget tech stack

---

## Dependencies & Execution Order

- T001 — setup, no deps
- T002 → T003 → T004 — foundational, sequential (same file); must complete before any US
- T005 → T006 → T007 — US1 CSS, sequential (same file)
- T008 → T009 → T010 → T011 — US1 JS, sequential (same file)
- T005–T007 and T008–T011 — parallel with each other ([P] CSS vs JS)
- T012 → T013 → T014 → T015 → T016 — US2 JS, sequential (same file); T005–T011 must be done
- T017 — US2 CSS, can run alongside US2 JS tasks [P]
- T018 → T019 → T020 → T021 → T022 → T023 — US3 JS, sequential
- T024 — US3 CSS, can run alongside US3 JS tasks [P]
- T025, T026, T027, T028 — polish, all parallel

---

## Implementation Strategy

### MVP (US1 + US2)

1. T001 — setup
2. T002 → T003 → T004 — config injection + tests
3. T005–T011 — button + panel open/close
4. T012–T017 — streaming chat
5. **Validate**: `mkdocs serve`, open chat, ask a question

### Full Delivery

6. T018–T024 — draggable button
7. T025–T028 — polish

**Total tasks**: 28
**MVP tasks**: 17 (T001–T017)
