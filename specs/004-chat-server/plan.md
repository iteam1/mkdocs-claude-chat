# Implementation Plan: Chat Server

**Branch**: `004-chat-server` | **Date**: 2026-03-27 | **Spec**: [spec.md](spec.md)

## Summary

Implement `src/mkdocs_claude_chat/_internal/server.py` — a FastAPI application with two endpoints:

- `POST /chat` — accepts `{ question, llmstxt_url }`, runs a `ClaudeSDKClient` session, streams the answer back as SSE (`text/event-stream`)
- `GET /health` — returns HTTP 200

Also expose a `run(port)` function that starts the uvicorn server; this will be called by `plugin.py` during `on_serve`.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `fastapi`, `uvicorn`, `anyio`, `claude-agent-sdk>=0.1.50` (already in `pyproject.toml`)
**Storage**: N/A — stateless per-request
**Testing**: pytest + `httpx` (async test client for FastAPI)
**Target Platform**: Local dev machine running `mkdocs serve`
**Project Type**: MkDocs plugin sidecar HTTP server
**Performance Goals**: First chunk within 3 seconds; single concurrent user
**Constraints**: CORS must allow all origins; port configurable (default `8001`); stateless

## Constitution Check

| Rule (Constitution §) | Status | Notes |
|---|---|---|
| §II — `_internal/` only | ✅ | `server.py` lives in `_internal/` |
| §V — `ClaudeSDKClient`, no custom tools | ✅ | `llmstxt_url` passed via system prompt only |
| §V — System prompt from `CLAUDE.md` strategy | ✅ | Check llms.txt → traverse → fallback |
| §VII — `from __future__ import annotations` | ✅ | Required |
| §VII — Full type annotations | ✅ | All functions annotated |
| §VIII — `get_logger(__name__)` | ✅ | Module-level `_logger` |
| §XIV — No standalone server independent of MkDocs | ✅ | `run()` called by plugin only |
| §X — Google docstring convention | ✅ | Applied |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-chat-server/
├── plan.md         ← this file
├── research.md
├── contracts/
│   └── chat-api.md ← SSE contract
└── tasks.md        ← /speckit.tasks
```

### Source Code

```text
src/mkdocs_claude_chat/_internal/
└── server.py           ← new implementation

tests/
└── test_server.py      ← async tests with httpx
```

---

## Phase 0: Research

One unknown: how to stream SSE from FastAPI with `ClaudeSDKClient`. Resolved below.

See [research.md](research.md).

---

## Phase 1: Design

### Request / Response models

```
ChatRequest:
  question:    str   (required)
  llmstxt_url: str   (default "")

SSE event (text chunk):
  data: {"text": "<chunk>"}\n\n

SSE sentinel:
  data: [DONE]\n\n

Error SSE:
  data: {"error": "<message>"}\n\n
  data: [DONE]\n\n
```

### System prompt template

```
You are a helpful assistant answering questions about a documentation site.

{llmstxt_hint}

1. Check {llmstxt_url} — if it exists, use it as the index (see https://llmstxt.org/)
2. Traverse links in llms.txt with curl/WebFetch to find relevant sections
3. If no llms.txt, fall back to WebFetch or WebSearch

Be concise and accurate. Quote or reference specific sections when possible.
```

Where `llmstxt_hint` is:
- `"The documentation index is available at: {llmstxt_url}"` — when url is non-empty
- `"No documentation index URL provided — use WebFetch or WebSearch."` — when empty

### FastAPI app structure

```
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

GET  /health  → 200 OK
POST /chat    → StreamingResponse(generator(), media_type="text/event-stream")

async def _stream_claude(question, llmstxt_url) -> AsyncIterator[str]:
    system_prompt = _build_system_prompt(llmstxt_url)
    client = ClaudeSDKClient(model=..., system_prompt=system_prompt)
    async with client.stream(question) as session:
        async for message in session:
            if AssistantMessage with TextBlock → yield SSE chunk
    yield "data: [DONE]\n\n"

def run(port: int = 8001) -> None:
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
```

### Test plan

| Test | What it checks |
|---|---|
| `test_health_returns_200` | `GET /health` → 200 |
| `test_chat_returns_sse_stream` | `POST /chat` → `content-type: text/event-stream` |
| `test_chat_stream_ends_with_done` | Last SSE event is `data: [DONE]` |
| `test_chat_missing_question_returns_422` | Missing body → HTTP 422 |
| `test_system_prompt_with_llmstxt_url` | Prompt contains the URL when provided |
| `test_system_prompt_without_llmstxt_url` | Prompt contains fallback text when empty |
