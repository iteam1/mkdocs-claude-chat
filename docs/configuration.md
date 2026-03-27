# Configuration

All options go under `plugins: claude-chat:` in `mkdocs.yml`.

## Full example

```yaml
plugins:
  - claude-chat:
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
  - claude-chat:
      enabled: !ENV [CLAUDE_CHAT_ENABLED, true]
```

---

### `model`

| Type | Default |
|---|---|
| `str` | `"claude-sonnet-4-6"` |

The Claude model used for answering questions. The model name is passed to the `claude-agent-sdk`.

```yaml
plugins:
  - claude-chat:
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
  - claude-chat:
      chat_title: "Ask the docs"
```

---

### `position`

| Type | Default |
|---|---|
| `str` | `"bottom-right"` |

Initial position of the floating chat button. Accepted values: `bottom-right`, `bottom-left`.

The button can also be dragged to any position by the user — this overrides the configured default for the current session.

```yaml
plugins:
  - claude-chat:
      position: bottom-left
```

---

### `llmstxt_url`

| Type | Default |
|---|---|
| `str` | `""` (auto-derived) |

URL of the site's [`llms.txt`](https://llmstxt.org/) index. Claude uses this file to discover and fetch relevant documentation sections before answering.

**Auto-detection**: if left empty and `site_url` is set in `mkdocs.yml`, the plugin derives:

```
llmstxt_url = <site_url>/llms.txt
```

Set explicitly when your `llms.txt` lives at a different path, or when serving locally without a `site_url`:

```yaml
plugins:
  - claude-chat:
      llmstxt_url: https://docs.example.com/llms.txt
```

---

### `system_prompt`

| Type | Default |
|---|---|
| `str` | `""` (built-in prompt used) |

Override the system prompt sent to Claude. The built-in prompt instructs Claude to:

1. Use the embedded `llms.txt` index (already in context) to identify all relevant pages
2. Fetch each relevant page via `curl` before answering — even for simple questions
3. For complex questions, fetch multiple pages and synthesize across them
4. Fall back to `llms-full.txt` grep or web search only if `curl` is unreachable

Use this to add domain-specific instructions:

```yaml
plugins:
  - claude-chat:
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
  - claude-chat:
      backend_port: 8080
```

The widget automatically sends requests to `http://localhost:<backend_port>` — no other config change needed.

---

### `session_ttl`

| Type | Default |
|---|---|
| `int` | `7200` |

Seconds of inactivity before a chat session is evicted from memory. When a session is evicted, the next message from that browser starts a fresh Claude conversation (the UI history is still shown, but Claude's memory resets).

Lower this to free up resources on shared machines; raise it for long documentation review sessions.

```yaml
plugins:
  - claude-chat:
      session_ttl: 3600   # 1 hour
```

---

### `max_sessions`

| Type | Default |
|---|---|
| `int` | `10` |

Maximum number of simultaneous live Claude sessions (i.e. concurrent `claude` CLI processes). When the limit is reached, the oldest idle session is evicted to make room.

```yaml
plugins:
  - claude-chat:
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
