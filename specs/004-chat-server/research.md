# Research: Chat Server

**Branch**: `004-chat-server` | **Date**: 2026-03-27

## Findings

| Decision | Choice | Rationale |
|---|---|---|
| HTTP framework | FastAPI | Already pulled in transitively; native async; `StreamingResponse` for SSE is idiomatic |
| SSE delivery | `StreamingResponse` with `media_type="text/event-stream"` | FastAPI built-in; no extra library needed |
| CORS | `fastapi.middleware.cors.CORSMiddleware` | Stdlib for FastAPI; `allow_origins=["*"]` for local dev |
| Server runner | `uvicorn.run(app, ...)` | Standard FastAPI production runner; already a transitive dep |
| Claude integration | `ClaudeSDKClient` with `system_prompt` | Constitution §V: no custom tools; llmstxt_url hint via prompt |
| Message parsing | `AssistantMessage` + `TextBlock` from `claude_agent_sdk.types` | SDK types for type-safe chunk extraction |
| Test client | `httpx.AsyncClient` with `app=app` | FastAPI's recommended async test pattern; no real server needed |

## Alternatives Considered

- **Starlette `EventSourceResponse`** (via `sse-starlette`) — cleaner SSE API but adds a dependency; `StreamingResponse` is sufficient
- **`aiohttp` server** — would require a separate dep and more boilerplate than FastAPI
- **Websockets** — overkill for a unidirectional stream; SSE is simpler and works without JS libraries
