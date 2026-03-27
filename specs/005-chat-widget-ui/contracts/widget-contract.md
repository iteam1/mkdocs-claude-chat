# Contract: Chat Widget

## Input — `window.__CLAUDE_CHAT_CONFIG__`

Injected by `plugin.py` via `on_post_page` as a `<script>` tag before `</body>`:

```js
window.__CLAUDE_CHAT_CONFIG__ = {
  backendUrl:  "http://localhost:8001",   // base URL of the chat server
  llmstxtUrl:  "https://example.com/llms.txt",  // may be ""
  chatTitle:   "Ask Claude",             // panel header text
  position:    "bottom-right"            // initial button position hint
};
```

All fields are always present. `llmstxtUrl` and `chatTitle` default to `""` / `"Ask Claude"` if not configured.

---

## Output — DOM Elements

The widget appends two elements to `<body>`:

```
#claude-chat-btn       — circular floating button
#claude-chat-panel     — side panel (hidden by default)
```

No existing DOM elements are modified. The widget only adds to `<body>`.

---

## Network — POST /chat

```
POST {backendUrl}/chat
Content-Type: application/json

{ "question": "<user text>", "llmstxt_url": "<llmstxtUrl from config>" }
```

Response: `text/event-stream` SSE (see `contracts/chat-api.md` in `004-chat-server`).

The widget reads chunks as:
```
data: {"text": "<chunk>"}    → append to current assistant message
data: {"error": "<msg>"}     → display error bubble, re-enable input
data: [DONE]                 → finalize message, re-enable input
```

---

## Drag State Contract

```
buttonX, buttonY  — current center position (px from viewport top-left)
isDragging        — true while pointer is captured
dragStartX/Y      — pointerdown coords
```

A drag is confirmed when `Math.hypot(dx, dy) >= 5` px at `pointerup`.
If distance < 5 px → treat as click (toggle panel).

---

## Config Injection Hook

`plugin.py` adds `on_post_page(output, *, page, config, **kwargs)` that:

1. Builds the config dict (same data as `claude_chat_config` from `on_page_context`)
2. Serializes to JSON
3. Inserts `<script>window.__CLAUDE_CHAT_CONFIG__ = {json};</script>` before the closing `</body>` tag
4. Returns the modified HTML string
