# Configuration

All options go under `plugins: ask-claude:` in `mkdocs.yml`.

## Full example

```yaml
plugins:
  - ask-claude:
      enabled: true
      model: claude-sonnet-4-6
      chat_title: "Ask Claude"
      position: bottom-right
      llmstxt_url: ""
      system_prompt: ""
      backend_port: 8001
      session_ttl: 7200
      max_sessions: 10
```

## Options

### `enabled`

| Type | Default |
|---|---|
| `bool` | `true` |

Set to `false` to disable the plugin entirely — no assets are injected, no server is started, and all hooks are skipped. Useful for disabling in production builds:

```yaml
plugins:
  - ask-claude:
      enabled: !ENV [CLAUDE_CHAT_ENABLED, true]
```

---

### `model`

| Type | Default |
|---|---|
| `str` | `"claude-sonnet-4-6"` |

The Claude model name passed to `claude-agent-sdk` for answering questions.

```yaml
plugins:
  - ask-claude:
      model: claude-opus-4-6    # more capable, slower
```

---

### `chat_title`

| Type | Default |
|---|---|
| `str` | `"Ask Claude"` |

Text displayed in the chat panel header.

```yaml
plugins:
  - ask-claude:
      chat_title: "Ask the docs"
```

---

### `position`

| Type | Default |
|---|---|
| `str` | `"bottom-right"` |

Initial position of the floating chat button. The button can also be dragged to any position by the user — the drag position overrides this setting for the current page load.

```yaml
plugins:
  - ask-claude:
      position: bottom-left
```

---

### `llmstxt_url`

| Type | Default |
|---|---|
| `str` | `""` (auto-derived) |

URL of the site's [`llms.txt`](https://llmstxt.org/) index. This value is embedded in each page's `window.__CLAUDE_CHAT_CONFIG__` and sent to the backend by the widget, but the **backend reads the actual docs directly from disk** — the URL is only used as a reference in the built-in system prompt's fallback instructions.

**Auto-detection**: if left empty:

- During `mkdocs serve`: derived from `dev_addr` + `site_url` path, e.g. `http://127.0.0.1:8000/llms.txt`
- During `mkdocs build`: derived from `site_url`, e.g. `https://example.com/llms.txt`

Set explicitly when your setup differs:

```yaml
plugins:
  - ask-claude:
      llmstxt_url: https://docs.example.com/llms.txt
```

---

### `system_prompt`

| Type | Default |
|---|---|
| `str` | `""` (built-in prompt used) |

Override the system prompt sent to Claude at the start of every new session. When set, the built-in prompt is **replaced entirely** — the `llms.txt` index is not automatically embedded.

The built-in prompt (used when this option is empty):

1. Reads `llms.txt` from disk and embeds the full index at the top of the prompt
2. Instructs Claude to identify all relevant pages from the index
3. Fetches each relevant page via `curl <url>/index.md` before answering
4. For complex questions, fetches multiple pages and synthesizes across them
5. Falls back to `llms-full.txt` grep if `curl` is unreachable

Use this option to add domain-specific instructions instead of the built-in documentation assistant behaviour:

```yaml
plugins:
  - ask-claude:
      system_prompt: |
        You are a helpful assistant for Acme Corp's internal API docs.
        Always recommend the v2 API endpoints over deprecated v1 ones.
        When in doubt, refer users to the support team at help@acme.com.
```

---

### `backend_port`

| Type | Default |
|---|---|
| `int` | `8001` |

TCP port the FastAPI chat server listens on. Change this if port `8001` is already in use on your machine.

```yaml
plugins:
  - ask-claude:
      backend_port: 8080
```

The widget automatically sends requests to `http://localhost:<backend_port>/chat` — no other config change needed.

---

### `session_ttl`

| Type | Default |
|---|---|
| `int` | `7200` |

Seconds of inactivity before a chat session is evicted from memory. When a session is evicted, the next message from that browser starts a fresh Claude conversation (the UI history stored in `sessionStorage` is still shown, but Claude's conversation memory resets).

Lower this value to free up resources; raise it for longer documentation review sessions.

```yaml
plugins:
  - ask-claude:
      session_ttl: 3600   # 1 hour
```

---

### `max_sessions`

| Type | Default |
|---|---|
| `int` | `10` |

Maximum number of simultaneous live Claude sessions (concurrent `ClaudeSDKClient` worker tasks). When the limit is reached, the oldest idle session is evicted to make room.

```yaml
plugins:
  - ask-claude:
      max_sessions: 5    # stricter limit on low-memory machines
```

---

## Widget customisation (CSS)

The widget exposes CSS custom properties at `:root` level. Override them in your theme's extra CSS:

```css
:root {
  --cc-primary: #0066cc;          /* button and send button color */
  --cc-primary-hover: #0052a3;    /* hover state */
  --cc-bg: #ffffff;               /* panel background */
  --cc-surface: #f5f5f5;          /* header and input row background */
  --cc-text: #1a1a1a;             /* primary text */
  --cc-text-muted: #666666;       /* secondary text */
  --cc-border: #e0e0e0;           /* dividers */
  --cc-radius: 14px;              /* bubble border radius */
}
```

Add your custom CSS file in `mkdocs.yml`:

```yaml
extra_css:
  - stylesheets/extra.css
```
