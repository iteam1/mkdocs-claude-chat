# Feature Specification: Chat Server

**Feature Branch**: `004-chat-server`
**Created**: 2026-03-27
**Status**: Draft
**Input**: User description: "server.py"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Visitor receives a streamed answer to their question (Priority: P1)

A documentation site visitor types a question in the chat widget and sees Claude's answer appear word-by-word, in real time, without waiting for the full response.

**Why this priority**: This is the core user-facing value of the entire plugin. Without it nothing works.

**Independent Test**: Send `POST /chat` with `{ "question": "What is this?", "llmstxt_url": "" }` and verify the response is a valid SSE stream that ends with `data: [DONE]`.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** a `POST /chat` request is sent with a valid question, **Then** the response streams SSE chunks and ends with `data: [DONE]`
2. **Given** a `llmstxt_url` is provided, **When** Claude processes the question, **Then** the URL is used as a hint to locate the documentation index
3. **Given** no `llmstxt_url` is provided, **When** Claude processes the question, **Then** Claude falls back to WebFetch or WebSearch
4. **Given** a malformed request body, **When** `POST /chat` is called, **Then** the server returns HTTP 422

---

### User Story 2 — Plugin confirms the server is ready before serving pages (Priority: P2)

When `mkdocs serve` starts, the plugin waits for the chat server to be ready before declaring itself healthy, so the widget is always available when the first page loads.

**Why this priority**: Without a health check, the widget may try to call the server before it is ready.

**Independent Test**: Send `GET /health` to the running server and verify HTTP 200 is returned immediately.

**Acceptance Scenarios**:

1. **Given** the server has started, **When** `GET /health` is called, **Then** HTTP 200 is returned
2. **Given** the server has not started yet, **When** the plugin polls `/health`, **Then** it retries until the server is ready or a timeout is reached

---

### Edge Cases

- What if the Claude CLI is not installed or not authenticated?
- What if port `8001` is already in use?
- What if the SSE stream is interrupted mid-response?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The server MUST expose `POST /chat` accepting `{ question, llmstxt_url }` and returning an SSE stream
- **FR-002**: Each SSE event MUST carry `{ "text": "<chunk>" }`; the stream MUST end with `data: [DONE]`
- **FR-003**: The server MUST expose `GET /health` returning HTTP 200 when ready
- **FR-004**: The server MUST include CORS headers allowing requests from any origin
- **FR-005**: The server MUST run on a configurable port (default `8001`)
- **FR-006**: The server MUST pass `llmstxt_url` as a hint in the Claude system prompt using the strategy defined in `CLAUDE.md`
- **FR-007**: The server MUST return HTTP 422 for missing or invalid request bodies
- **FR-008**: The server MUST return HTTP 500 if the Claude session fails, with an error message in the SSE stream

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: First text chunk appears within 3 seconds of the request being received
- **SC-002**: The full answer streams correctly end-to-end without dropped chunks
- **SC-003**: `GET /health` responds in under 100ms
- **SC-004**: Invalid requests receive an error response — the server never crashes on bad input

## Assumptions

- The `claude` CLI is installed and authenticated in the environment where `mkdocs serve` runs
- The server is only used during `mkdocs serve` (local dev) — not in production static builds
- A single concurrent user per dev session is the expected load — no connection pooling needed
- The plugin is responsible for starting and stopping the server process
