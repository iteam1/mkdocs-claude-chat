# Installation

## Prerequisites

### 1. Claude Code CLI

The plugin uses Claude through the `claude` CLI. If you already use Claude Code, you are done. Otherwise:

1. Download and install from **[claude.ai/code](https://claude.ai/code)**
2. Log in:

```bash
claude login
```

3. Confirm it works:

```bash
claude --version
```

That's the only credential setup you will ever need. The plugin inherits whatever account the CLI is logged in to — no API keys, no environment variables.

---

### 2. Python 3.10+ and MkDocs 1.5+

```bash
pip install mkdocs
```

---

## Install the plugins

`mkdocs-claude-chat` and `mkdocs-llmstxt` are designed to work as a pair:

- **`mkdocs-llmstxt`** generates `site/llms.txt` — a structured index of every page in your docs
- **`mkdocs-claude-chat`** reads that index and gives it to Claude, so Claude knows your entire docs structure before the first question

Install both together:

```bash
pip install mkdocs-llmstxt git+https://github.com/iteam1/mkdocs-claude-chat
```

Or with `uv`:

```bash
uv add mkdocs-llmstxt git+https://github.com/iteam1/mkdocs-claude-chat
```

---

## Add to mkdocs.yml

Minimal configuration:

```yaml
plugins:
  - search
  - llmstxt
  - claude-chat
```

> **Order matters** — `llmstxt` must come before `claude-chat` so the index is built before the chat backend reads it.

If you want to include all pages in the index automatically:

```yaml
plugins:
  - search
  - llmstxt:
      full_output: llms-full.txt   # also write a single merged file (fallback)
      sections:
        Docs:
          - "**"                   # include every .md file
  - claude-chat
```

---

## Verify

```bash
mkdocs serve
```

You should see:

```
INFO    -  claude-chat: starting chat backend on http://localhost:8001
INFO    -  Building documentation...
INFO    -  Serving on http://127.0.0.1:8000/
```

Open your browser — a floating chat button appears at the bottom-right corner of every page.

Send a question. Claude will:
1. Check its embedded `llms.txt` index (already in context — no fetch needed)
2. Fetch the relevant pages via `curl`
3. Stream a synthesized answer

You can watch step 2 happen in real time — each `curl` call appears as a collapsible tool block in the chat panel.

---

## Next step

[Quick Start →](quickstart.md) — a complete working example with all config options explained.
