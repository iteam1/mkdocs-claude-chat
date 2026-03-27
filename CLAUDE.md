# CLAUDE.md

## Handle documentation links

When a user asks a question and a documentation URL is available:

1. Check `<url>/llms.txt` — if it exists, use it as the index (read https://llmstxt.org/ for more information)
2. Traverse links in `llms.txt` with `curl` + `grep` to find relevant sections
3. If no `llms.txt`, fall back to WebFetch, WebSearch, or Playwright

## Active Technologies
- Python 3.10+ + stdlib `logging` only — no new packages (001-logger-adapter)
- Python 3.10+ + `shutil`, `pathlib` (stdlib only) — no new packages (002-assets-injection)
- Filesystem — reads from package `assets/`, writes to `site_dir/assets/` (002-assets-injection)
- Python 3.10+ + `mkdocs>=1.5`, `logger.py` (001), `assets.py` (002) — no new packages (003-plugin-hooks)
- N/A (reads config, writes to template context) (003-plugin-hooks)
- Python 3.10+ + `fastapi`, `uvicorn`, `anyio`, `claude-agent-sdk>=0.1.50` (already in `pyproject.toml`) (004-chat-server)
- N/A — stateless per-request (004-chat-server)
- JavaScript ES2020+ (no transpiler), CSS3 custom properties + None — vanilla JS + CSS, no external libraries (005-chat-widget-ui)
- In-memory JS module scope only (chat history, drag position) (005-chat-widget-ui)

## Recent Changes
- 001-logger-adapter: Added Python 3.10+ + stdlib `logging` only — no new packages
