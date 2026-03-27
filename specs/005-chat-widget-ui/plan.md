# Implementation Plan: Chat Widget UI

**Branch**: `005-chat-widget-ui` | **Date**: 2026-03-27 | **Spec**: [spec.md](spec.md)

## Summary

Implement `src/mkdocs_claude_chat/assets/chat.js` and `chat.css` — a self-contained vanilla JS/CSS widget that:

- Renders a draggable circular button floating over every MkDocs page
- Opens a right-side chat panel that streams Claude answers via SSE
- Reads all config from `window.__CLAUDE_CHAT_CONFIG__` injected by `plugin.py`

Also add `on_post_page` hook to `plugin.py` to inject the config script tag into every page's HTML.

## Technical Context

**Language/Version**: JavaScript ES2020+ (no transpiler), CSS3 custom properties
**Primary Dependencies**: None — vanilla JS + CSS, no external libraries
**Storage**: In-memory JS module scope only (chat history, drag position)
**Testing**: Manual browser testing during `mkdocs serve`
**Target Platform**: Modern browsers (Chrome 90+, Firefox 90+, Safari 14+, Edge 90+)
**Project Type**: Frontend widget (static assets bundled with MkDocs plugin)
**Performance Goals**: Panel animation ≤ 300 ms; first SSE chunk appears ≤ 5 s (local dev)
**Constraints**: Zero layout shift to existing page content; no external CDN deps; single `chat.js` + `chat.css`

## Constitution Check

| Rule (Constitution §) | Status | Notes |
|---|---|---|
| §II — assets live in `assets/` | ✅ | `chat.js` and `chat.css` in `src/mkdocs_claude_chat/assets/` |
| §II — implementation in `_internal/` | ✅ | `on_post_page` hook added to `plugin.py` in `_internal/` |
| §V — no custom tools | ✅ | Widget calls backend via HTTP; Claude's built-in tools used server-side |
| §XIV — no standalone server | ✅ | Widget only; server managed by plugin |
| §IX — coverage ≥ 90% | ⚠️ | JS has no automated tests; Python `on_post_page` hook covered by `test_plugin.py` |

No violations. The §IX note applies to JS only — Python coverage target is maintained.

## Project Structure

### Documentation (this feature)

```text
specs/005-chat-widget-ui/
├── plan.md             ← this file
├── research.md
├── contracts/
│   └── widget-contract.md
└── tasks.md            ← /speckit.tasks
```

### Source Code

```text
src/mkdocs_claude_chat/
├── assets/
│   ├── chat.css        ← new: widget styles
│   └── chat.js         ← new: widget logic
└── _internal/
    └── plugin.py       ← modify: add on_post_page hook

tests/
└── test_plugin.py      ← modify: add on_post_page tests
```

---

## Phase 0: Research

See [research.md](research.md). All decisions resolved — no NEEDS CLARIFICATION items.

---

## Phase 1: Design

### Config Injection (`plugin.py` → `on_post_page`)

```python
def on_post_page(self, output: str, *, page: Page, config: MkDocsConfig, **kwargs: object) -> str | None:
    if not self.config.enabled:
        return None
    cfg = {
        "backendUrl": "http://localhost:8001",
        "llmstxtUrl": self._llmstxt_url,
        "chatTitle":  self.config.chat_title,
        "position":   self.config.position,
    }
    script = f'<script>window.__CLAUDE_CHAT_CONFIG__ = {json.dumps(cfg)};</script>'
    return output.replace("</body>", f"{script}\n</body>", 1)
```

### Widget Structure (`chat.js`)

```
Module-level state:
  cfg          — window.__CLAUDE_CHAT_CONFIG__
  panelOpen    — bool
  buttonX/Y    — drag position (px)
  isDragging   — bool
  messages     — [{role, text}]

Functions:
  init()               — build DOM, attach events, called on DOMContentLoaded
  createButton()       — build #claude-chat-btn
  createPanel()        — build #claude-chat-panel (header, messages, input row)
  togglePanel()        — flip panelOpen, apply CSS class
  sendMessage()        — read input, POST to backend, stream response
  streamResponse(q)    — fetch + ReadableStream + TextDecoder, yield SSE chunks
  appendMessage(role, text)  — add bubble to messages area
  appendChunk(text)    — append text to last assistant bubble
  clampPosition(x, y) — enforce viewport bounds
  onPointerDown(e)     — record drag start
  onPointerMove(e)     — move button if dragging
  onPointerUp(e)       — confirm drag or fire click
```

### Panel Layout (`chat.css`)

```
#claude-chat-btn
  position: fixed
  width/height: 56px, border-radius: 50%
  z-index: 9999
  cursor: grab / grabbing during drag
  transition: box-shadow 0.15s

#claude-chat-panel
  position: fixed
  top: 0, right: 0, height: 100vh
  width: 360px (100vw on ≤ 480px)
  transform: translateX(100%)   ← hidden
  transition: transform 0.25s ease
  z-index: 9998
  display: flex, flex-direction: column

#claude-chat-panel.open
  transform: translateX(0)      ← visible

.cc-messages
  flex: 1, overflow-y: auto

.cc-input-row
  display: flex, gap: 8px

.cc-bubble-user / .cc-bubble-assistant
  border-radius: 12px, padding: 8px 12px
  max-width: 80%
```

### SSE Streaming (`chat.js` `streamResponse`)

```js
async function* streamResponse(question) {
  const res = await fetch(`${cfg.backendUrl}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, llmstxt_url: cfg.llmstxtUrl }),
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const lines = buf.split("\n");
    buf = lines.pop();         // keep incomplete line
    for (const line of lines) {
      if (line.startsWith("data: ")) yield line.slice(6).trim();
    }
  }
}
```

### Test Plan

| Test | File | What it checks |
|---|---|---|
| `test_on_post_page_injects_script` | `test_plugin.py` | Script tag with JSON config present in output |
| `test_on_post_page_disabled` | `test_plugin.py` | Returns None when `enabled: false` |
| `test_on_post_page_config_values` | `test_plugin.py` | `backendUrl`, `llmstxtUrl`, `chatTitle`, `position` are correct |
