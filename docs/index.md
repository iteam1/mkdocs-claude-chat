# mkdocs-claude-chat

**Add a Claude-powered chatbot to your MkDocs site — Claude reads YOUR docs, not the internet.**

Visitors ask questions in natural language. Claude fetches the relevant pages from your own documentation, synthesizes the answer, and streams it back word-by-word.

---

## How it works

```
User asks a question
      │
      ▼
Chat widget  →  FastAPI sidecar  →  Claude (via claude-agent-sdk)
                                         │
                              reads llms.txt page index
                              fetches relevant doc pages
                              synthesizes answer across pages
                                         │
                              streams answer back  ←─────────┘
```

1. `mkdocs-llmstxt` builds `site/llms.txt` — a structured index of every page in your docs
2. `claude-chat` embeds that index in Claude's system prompt at session start
3. Claude knows your entire docs structure before the first question
4. For each question, Claude identifies the relevant pages, fetches them, and synthesizes a complete answer

---

## Quick install

```bash
pip install mkdocs-llmstxt git+https://github.com/iteam1/mkdocs-claude-chat
```

Add to `mkdocs.yml`:

```yaml
plugins:
  - search
  - llmstxt
  - claude-chat
```

Run:

```bash
mkdocs serve
```

A chat button appears on every page. Claude already knows your docs — no URL, no API key, no extra configuration.

---

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.10+ | |
| MkDocs 1.5+ | `pip install mkdocs` |
| Claude Code CLI | Install from [claude.ai/code](https://claude.ai/code), then `claude login` |

The plugin drives Claude through the `claude-agent-sdk`. As long as the `claude` CLI is authenticated on your machine, it just works.

---

## Features

- **Reads your docs** — Claude uses `llms.txt` to know every page, fetches only what's relevant
- **Multi-page synthesis** — for complex questions Claude fetches several pages and combines the answer
- **Streamed answers** — text appears as Claude writes it
- **Live tool call feed** — see which pages Claude is fetching in real time, collapsible
- **Persistent session** — conversation survives page navigation within the same tab
- **Draggable widget** — move the chat button anywhere on screen
- **Resizable panel** — drag the left edge to adjust width
- **No layout shift** — the panel overlays your docs without reflowing content
- **Theme-neutral** — works with Material, ReadTheDocs, MkDocs default, or any custom theme

---

## Next steps

- **[Installation →](getting-started/installation.md)** — full setup with prerequisites
- **[Quick Start →](getting-started/quickstart.md)** — working chat in 5 minutes
- **[Configuration →](configuration.md)** — model, title, position, custom system prompt
- **[Troubleshooting →](troubleshooting.md)** — common issues and fixes
