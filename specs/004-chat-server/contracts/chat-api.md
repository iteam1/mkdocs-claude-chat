# Contract: Chat Server API

## POST /chat

**Request**
```json
{ "question": "string (required)", "llmstxt_url": "string (default '')" }
```

**Response** — `text/event-stream`
```
data: {"text": "<chunk>"}\n\n
...
data: [DONE]\n\n
```

**Errors**
```
HTTP 422 — missing/invalid body
HTTP 500 — Claude session failure → data: {"error": "..."}\n\ndata: [DONE]\n\n
```

**Headers**
```
Access-Control-Allow-Origin: *
```

---

## GET /health

**Response** — `200 OK`
