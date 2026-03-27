# Quick Start

A complete working MkDocs site with Claude chat in 5 minutes.

---

## Step 1 — Install

```bash
pip install git+https://github.com/iteam1/mkdocs-ask-claude
pip install mkdocs-llmstxt
```

Make sure the Claude CLI is logged in:

```bash
claude login      # only needed once
claude --version  # confirm
```

---

## Step 2 — Configure mkdocs.yml

```yaml
site_name: My Docs

plugins:
  - search
  - llmstxt:
      full_output: llms-full.txt
      sections:
        Docs:
          - "**"          # index every page automatically
  - ask-claude:
      chat_title: "Ask the docs"
```

That is the complete configuration. Everything else is automatic.

---

## Step 3 — Serve

```bash
mkdocs serve
```

Open [http://localhost:8000](http://localhost:8000) and click the chat button.

---

## What happens automatically

When `mkdocs serve` starts:

1. **`mkdocs-llmstxt` builds `site/llms.txt`** — a structured index listing every page URL and its description
2. **`ask-claude` reads that file from disk** and embeds the full index into Claude's system prompt
3. **A FastAPI backend starts on `http://localhost:8001`** — the widget sends questions here
4. Claude now has a complete map of your docs **before the first message is sent**

When a visitor asks a question:

1. The widget POSTs the question to `http://localhost:8001/chat` with a session ID
2. The backend forwards the question to a dedicated `ClaudeSDKClient` worker for that session
3. Claude scans the index it already has to identify relevant pages
4. For complex questions, Claude identifies **multiple** relevant pages
5. Each page is fetched via `Bash` (`curl`) or `WebFetch` — you can watch this happen live in the chat panel as collapsible tool blocks
6. Claude synthesizes the answer across all fetched pages and streams it back as SSE

---

## Trying it out

Here are some questions that exercise multi-page synthesis well:

- *"How do I get started with this project end-to-end?"*
- *"What are all the configuration options and what do they do?"*
- *"Walk me through how X works internally"*

For these, Claude will fetch 3–6 pages and combine the answers — you will see each tool call appear in the chat as it happens.

---

## Customise the widget

```yaml
plugins:
  - ask-claude:
      chat_title: "Ask Claude"       # panel header text
      position: bottom-right         # or bottom-left
      model: claude-sonnet-4-6       # default model
      backend_port: 8001             # change if port is taken
```

### Custom CSS

The widget uses CSS custom properties. Add an extra stylesheet to restyle it:

```css
/* docs/stylesheets/extra.css */
:root {
  --cc-primary: #0066cc;
  --cc-bg: #ffffff;
  --cc-radius: 10px;
}
```

```yaml
extra_css:
  - stylesheets/extra.css
```

---

## Disable in production

The plugin is intended for local `mkdocs serve`. Disable it in CI or production builds with an environment variable:

```yaml
plugins:
  - ask-claude:
      enabled: !ENV [CLAUDE_CHAT_ENABLED, false]
```

```bash
CLAUDE_CHAT_ENABLED=true mkdocs serve   # enable locally
mkdocs build                            # disabled by default
```

---

## Next steps

- [All configuration options →](../configuration.md)
- [Troubleshooting →](../troubleshooting.md)
