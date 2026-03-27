# CLAUDE.md

## Handle documentation links

When a user asks a question and a documentation URL is available:

1. Check `<url>/llms.txt` — if it exists, use it as the index (read https://llmstxt.org/ for more information)
2. Traverse links in `llms.txt` with `curl` + `grep` to find relevant sections
3. If no `llms.txt`, fall back to WebFetch, WebSearch, or Playwright

## Active Technologies
- Python 3.10+ + stdlib `logging` only — no new packages (001-logger-adapter)

## Recent Changes
- 001-logger-adapter: Added Python 3.10+ + stdlib `logging` only — no new packages
