# Quick Start

Get a Claude-powered chat widget running on your MkDocs site in under 5 minutes.

## 1. Install

```bash
pip install mkdocs-claude-chat
```

## 2. Enable the plugin

Edit your `mkdocs.yml`:

```yaml
site_name: My Docs
plugins:
  - search
  - claude-chat
```

## 3. Serve

```bash
mkdocs serve
```

Open [http://localhost:8000](http://localhost:8000) — you'll see a **chat button** in the bottom-right corner.

## 4. Ask a question

Click the button, type a question about your documentation, and press **Enter**.

Claude reads your docs and streams an answer back word-by-word.

---

## Customise the widget

```yaml
plugins:
  - claude-chat:
      chat_title: "Ask the docs"
      position: bottom-right        # or bottom-left
      model: claude-sonnet-4-6
```

## Point Claude at your llms.txt

If your site has an `llms.txt` index (e.g. via `mkdocs-llmstxt`), tell the plugin:

```yaml
plugins:
  - claude-chat:
      llmstxt_url: https://your-site.example.com/llms.txt
```

Claude will use it as the primary knowledge source before falling back to web search.

If `llmstxt_url` is not set and your `mkdocs.yml` has a `site_url`, the plugin auto-derives it as `<site_url>/llms.txt`.

---

## What happens behind the scenes

```
mkdocs serve
    │
    ├── Plugin injects chat.js + chat.css into every page
    ├── Plugin starts FastAPI sidecar on port 8001
    │
    └── Browser loads page
            │
            ├── Chat button appears (bottom-right)
            └── User asks a question
                    │
                    └── POST http://localhost:8001/chat
                                │
                                └── Claude reads llms.txt → fetches pages → streams answer
```

---

## Next steps

- [All configuration options →](../configuration.md)
- [Chat server API →](../reference/api.md)
- [Architecture →](../reference/architecture.md)
