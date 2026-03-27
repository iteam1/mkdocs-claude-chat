# Tasks: Chat Server

**Input**: Design documents from `/specs/004-chat-server/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, contracts/chat-api.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

- [ ] T001 Verify `src/mkdocs_claude_chat/_internal/server.py` exists as a stub
- [ ] T002 Install `httpx` into the venv for async test client: `uv pip install httpx --python .venv/bin/python`

---

## Phase 2: Foundational

- [ ] T003 Add module-level imports (`fastapi`, `uvicorn`, `anyio`, `claude_agent_sdk`), `_logger`, and the `ChatRequest` Pydantic model to `src/mkdocs_claude_chat/_internal/server.py`
- [ ] T004 Implement `_build_system_prompt(llmstxt_url: str) -> str` that returns the prompt with the llmstxt hint or fallback text in `src/mkdocs_claude_chat/_internal/server.py`
- [ ] T005 Create the FastAPI `app` instance and add `CORSMiddleware` with `allow_origins=["*"]` in `src/mkdocs_claude_chat/_internal/server.py`

**Checkpoint**: App skeleton ready — user story implementation can begin.

---

## Phase 3: User Story 1 — Visitor receives a streamed answer (Priority: P1) 🎯 MVP

**Goal**: `POST /chat` accepts a question, runs `ClaudeSDKClient`, and streams SSE chunks ending with `data: [DONE]`.

**Independent Test**: `POST /chat` with `{ "question": "hi", "llmstxt_url": "" }` → `content-type: text/event-stream`, stream ends with `data: [DONE]`.

- [ ] T006 [US1] Implement `_stream_claude(question, llmstxt_url)` async generator that runs `ClaudeSDKClient`, yields `data: {"text": "..."}` SSE chunks, and yields `data: [DONE]` at the end in `src/mkdocs_claude_chat/_internal/server.py`
- [ ] T007 [US1] Implement `POST /chat` route that validates `ChatRequest` and returns `StreamingResponse(_stream_claude(...), media_type="text/event-stream")` in `src/mkdocs_claude_chat/_internal/server.py`
- [ ] T008 [US1] Add error handling in `_stream_claude` — on exception yield `data: {"error": "..."}` then `data: [DONE]` in `src/mkdocs_claude_chat/_internal/server.py`

**Checkpoint**: Streaming chat endpoint complete — US1 done.

---

## Phase 4: User Story 2 — Plugin confirms server is ready (Priority: P2)

**Goal**: `GET /health` returns HTTP 200; `run(port)` starts uvicorn.

**Independent Test**: `GET /health` → 200 OK.

- [ ] T009 [US2] Implement `GET /health` route returning `{"status": "ok"}` in `src/mkdocs_claude_chat/_internal/server.py`
- [ ] T010 [US2] Implement `run(port: int = 8001) -> None` that calls `uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")` in `src/mkdocs_claude_chat/_internal/server.py`
- [ ] T011 [US2] Add Google-style docstrings to all public functions and the `ChatRequest` model in `src/mkdocs_claude_chat/_internal/server.py`

**Checkpoint**: Both endpoints complete — US1 and US2 done.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T012 [P] Write unit tests in `tests/test_server.py` using `httpx.AsyncClient(app=app)` — mock `ClaudeSDKClient` to avoid real CLI calls — covering: health 200, chat SSE stream, `[DONE]` sentinel, 422 on missing body, system prompt with/without llmstxt_url

---

## Dependencies & Execution Order

- T001, T002 — parallel setup
- T003 → T004 → T005 — foundational, sequential (same file)
- T006 → T007 → T008 — US1, sequential (same file, depends on T003–T005)
- T009 → T010 → T011 — US2, sequential (same file, depends on T003–T005)
- T012 — after T011

---

## Implementation Strategy

### MVP (US1 + US2)

1. T001, T002 — setup
2. T003 → T004 → T005 — foundation
3. T006 → T007 → T008 — streaming chat
4. T009 → T010 → T011 — health + runner
5. T012 — tests

**Total tasks**: 12
**MVP tasks**: 11 (T001–T011)
