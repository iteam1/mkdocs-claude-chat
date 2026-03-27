# Installation

## Prerequisites

### 1. Claude Code CLI

The plugin uses Claude through the `claude` CLI via `claude-agent-sdk`. If you already use Claude Code, you are done. Otherwise:

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

`mkdocs-ask-claude` and `mkdocs-llmstxt` are designed to work as a pair:

- **`mkdocs-llmstxt`** generates `site/llms.txt` — a structured index of every page in your docs
- **`mkdocs-ask-claude`** reads that index from disk and embeds it into Claude's system prompt so Claude knows your entire docs structure before the first question

Install the plugin:

```bash
pip install git+https://github.com/iteam1/mkdocs-ask-claude
```

Or with `uv`:

```bash
uv pip install git+https://github.com/iteam1/mkdocs-ask-claude
```

Install the companion plugin that generates `llms.txt`:

```bash
pip install mkdocs-llmstxt
```

---

## Add to mkdocs.yml

Minimal configuration:

```yaml
plugins:
  - search
  - llmstxt
  - ask-claude
```

> **Order matters** — `llmstxt` must come before `ask-claude` so the index is written before the chat backend reads it at serve time.

If you want to include all pages in the index automatically and also generate a merged single-file fallback:

```yaml
plugins:
  - search
  - llmstxt:
      full_output: llms-full.txt   # also write a single merged file (fallback for Claude)
      sections:
        Docs:
          - "**"                   # include every .md file
  - ask-claude
```

---

## Verify

```bash
mkdocs serve
```

You should see:

```
INFO    -  ask-claude: starting chat backend on http://localhost:8001
INFO    -  Building documentation...
INFO    -  Serving on http://127.0.0.1:8000/
```

Open your browser — a floating chat button appears at the bottom-right corner of every page.

Send a question. Claude will:

1. Use the embedded `llms.txt` index (already in its system prompt — no fetch needed)
2. Identify the relevant pages
3. Fetch them via `curl` or `WebFetch`
4. Stream a synthesized answer

You can watch step 3 happen in real time — each tool call appears as a collapsible block in the chat panel.

---

## Next step

[Quick Start →](quickstart.md) — a complete working example with all config options explained.
