# mkdocs-ask-claude

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
                              reads llms.txt index from disk
                              fetches relevant doc pages (curl / WebFetch)
                              synthesizes answer across pages
                                         │
                              streams answer back  ←─────────┘
```

1. `mkdocs-llmstxt` builds `site/llms.txt` — a structured index of every page in your docs
2. `ask-claude` reads that index **from disk** and embeds it into Claude's system prompt at session start
3. Claude knows your entire docs structure before the first question
4. For each question, Claude identifies the relevant pages, fetches them, and synthesizes a complete answer

---

## Quick install

```bash
pip install git+https://github.com/iteam1/mkdocs-ask-claude
```

Add to `mkdocs.yml`:

```yaml
plugins:
  - search
  - llmstxt
  - ask-claude
```

Run:

```bash
mkdocs serve
```

A chat button appears on every page. Claude already knows your docs — no API key, no extra configuration.

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

- **Reads your docs** — Claude uses the `llms.txt` index (embedded in its system prompt) to know every page, then fetches only what is relevant via `curl` / `WebFetch`
- **Multi-page synthesis** — for complex questions Claude fetches several pages and combines the answer
- **Streamed answers** — text appears as Claude writes it
- **Live tool call feed** — see which pages Claude is fetching in real time, collapsible
- **Stateful sessions** — conversation history survives page navigation within the same browser tab
- **Draggable widget** — move the chat button anywhere on screen
- **Resizable panel** — drag the left edge to adjust width
- **Theme-neutral** — works with Material, ReadTheDocs, MkDocs default, or any custom theme

---

## Next steps

- **[Installation →](getting-started/installation.md)** — full setup with prerequisites
- **[Quick Start →](getting-started/quickstart.md)** — working chat in 5 minutes
- **[Configuration →](configuration.md)** — model, title, position, custom system prompt
- **[Troubleshooting →](troubleshooting.md)** — common issues and fixes
