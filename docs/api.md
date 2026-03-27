# Chat Server API

The chat server is a local HTTP sidecar spawned by the plugin during `mkdocs serve`.
It receives questions from the browser widget and streams Claude's answers back.

## Endpoints

### `POST /chat`

Send a question and receive a streamed response.

**Request**

```http
POST /chat
Content-Type: application/json

{
  "question": "How do I install this plugin?",
  "llmstxt_url": "https://example.org/llms.txt"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | string | yes | The user's question |
| `llmstxt_url` | string | no | URL of the site's `/llms.txt` index — passed as a hint to Claude |

**Response**

`Content-Type: text/event-stream`

Each event carries one text chunk as Claude produces it:

```
data: {"text": "You can install"}

data: {"text": " this plugin with pip:"}

data: {"text": " `pip install mkdocs-claude-chat`"}

data: [DONE]
```

The stream ends with a `data: [DONE]` sentinel. The client concatenates all `text` chunks to build the full response.

**Error response**

```
HTTP 422  — missing or invalid request body
HTTP 500  — Claude session failed
```

---

### `GET /health`

Liveness check used by the plugin to confirm the sidecar is ready before the first page load.

**Response**

```
HTTP 200 OK
```

---

## Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Streaming format | SSE (`text/event-stream`) | Words appear as Claude types — better UX than waiting for the full response |
| `llmstxt_url` ownership | Sent by JS per-request | More reliable — JS already has it from `window.__CLAUDE_CHAT_CONFIG__`; no server-side config needed |
| Default port | `8001` | Configurable via plugin `port` option; avoids conflict with MkDocs default (`:8000`) |
| CORS | Enabled | Widget JS on `:8000` calls server on `:8001` — `Access-Control-Allow-Origin: *` required |
