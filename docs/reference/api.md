# Chat Server API

The chat server is a local FastAPI sidecar spawned by the plugin during `mkdocs serve`.
It receives questions from the browser widget and streams Claude's answers back as Server-Sent Events.

The server listens on `http://127.0.0.1:<backend_port>` (default: `8001`).

## Endpoints

### `POST /chat`

Send a question and receive a streamed response.

**Request**

```http
POST /chat
Content-Type: application/json

{
  "question": "How do I install this plugin?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "system_prompt": "",
  "llmstxt_url": ""
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | string | yes | The user's question |
| `session_id` | string | no | Browser-generated UUID to maintain conversation history across multiple turns. Each browser tab generates one on first load and persists it in `sessionStorage`. |
| `system_prompt` | string | no | Optional override for the system prompt. If empty, the built-in documentation assistant prompt (with the embedded `llms.txt` index) is used. |
| `llmstxt_url` | string | no | Ignored by the server — kept for client compatibility. The server reads docs directly from disk. |

**Response**

`Content-Type: text/event-stream`

The stream emits JSON-encoded events of several types:

```
data: {"text": "You can install"}

data: {"text": " this plugin with pip:"}

data: {"tool_call": {"id": "toolu_01", "name": "Bash", "command": "curl -s http://127.0.0.1:8000/llms.txt"}}

data: {"tool_result": {"id": "toolu_01", "output": "# My Docs\n...", "is_error": false}}

data: {"text": " `pip install mkdocs-ask-claude`"}

data: [DONE]
```

| Event type | Payload | Description |
|---|---|---|
| `text` | `{"text": "..."}` | A text chunk from Claude's response |
| `tool_call` | `{"id": "...", "name": "Bash"\|"WebFetch"\|"WebSearch", "command": "..."}` | Claude is running a tool |
| `tool_result` | `{"id": "...", "output": "...", "is_error": false}` | Result returned to Claude from a tool call |
| `error` | `{"error": "..."}` | An error occurred during the request |

The stream ends with `data: [DONE]`. The client concatenates all `text` chunks to build the full response.

**Session behaviour**

- When `session_id` is provided, the server maintains a stateful `ClaudeSDKClient` worker task for that session ID. Subsequent messages in the same session are handled by the same worker, preserving full conversation history natively.
- When `session_id` is empty, a throw-away worker is created for that single request and torn down immediately after.

**Error responses**

```
HTTP 422  — missing or invalid request body (Pydantic validation failure)
```

Runtime errors (Claude session failures) are delivered as `data: {"error": "..."}` in the SSE stream, not as HTTP error codes.

---

### `GET /health`

Liveness check.

**Response**

```json
HTTP 200 OK

{"status": "ok"}
```

---

## Session management

The server maintains a `_sessions` dict of active `_ChatSession` objects. Each session holds:

- An asyncio `Queue` for sending questions to the worker
- An asyncio `Task` running the `ClaudeSDKClient` worker loop
- A `last_used` timestamp for TTL-based eviction

Sessions are evicted:

- After `session_ttl` seconds of inactivity (default: 7200 s)
- When `max_sessions` is reached — the oldest session is evicted to make room (default: 10)

---

## Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Streaming format | SSE (`text/event-stream`) | Words appear as Claude types — better UX than waiting for the full response |
| Docs loading | Filesystem reads at session start | Avoids network round-trips; works even without `site_url` configured |
| `llmstxt_url` in request | Accepted but ignored | Kept for client compatibility — the server always reads from disk |
| Default port | `8001` | Avoids conflict with MkDocs dev server (`:8000`); configurable via `backend_port` |
| CORS | `allow_origins=["*"]` | Widget JS on `:8000` calls server on `:8001` — cross-origin request |
| Session isolation | One asyncio Task per session | `ClaudeSDKClient` must be used from the same task that called `connect()` |
