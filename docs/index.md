# mkdocs-claude-chat

**A MkDocs plugin that adds a Claude-powered chatbot to your documentation site.**

Readers can ask questions in natural language and get accurate, streamed answers — Claude reads your docs through `llms.txt` so answers stay in context.

---

## How it works

```
Browser widget  →  POST /chat  →  FastAPI sidecar  →  Claude (built-in tools)
                                                              ↓
                                                       reads llms.txt
                                                       fetches doc pages
                                                       streams answer back
```

1. The plugin injects a floating chat button into every page
2. When a visitor asks a question, it's sent to a local FastAPI server (port 8001)
3. Claude reads your `/llms.txt` index and fetches relevant doc pages
4. The answer streams back word-by-word into the chat panel

---

## Quick install

```bash
pip install mkdocs-claude-chat
```

Add to `mkdocs.yml`:

```yaml
plugins:
  - search
  - claude-chat
```

Run:

```bash
mkdocs serve
```

That's it. A chat button appears at the bottom-right of every page.

---

## Requirements

| Requirement | Details |
|---|---|
| Python | 3.10+ |
| MkDocs | 1.5+ |
| Claude CLI | Must be installed and authenticated (`claude --version`) |

The plugin shells out to the `claude` CLI via `claude-agent-sdk`. No API key configuration needed if the CLI is already set up.

---

## Features

- **Streamed answers** — text appears as Claude types, no waiting
- **Draggable widget** — move the chat button anywhere on screen
- **`llms.txt` aware** — Claude uses your documentation index as its knowledge source
- **Zero layout shift** — the widget overlays your docs without affecting layout
- **Theme-customizable** — CSS custom properties for colors and radius
- **Works with any MkDocs theme** — no template overrides required

---

## Next steps

<div class="grid cards" markdown>

- :material-rocket-launch: **[Quick Start](getting-started/quickstart.md)**

    Get your first Claude-powered chat working in 5 minutes.

- :material-cog: **[Configuration](configuration.md)**

    All plugin options — model, position, title, custom system prompt.

- :material-api: **[API Reference](reference/api.md)**

    Chat server endpoints and SSE streaming protocol.

- :material-source-branch: **[Architecture](reference/architecture.md)**

    How the plugin modules fit together.

</div>
