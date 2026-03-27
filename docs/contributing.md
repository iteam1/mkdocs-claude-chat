# Contributing

## Development setup

```bash
git clone https://github.com/iteam1/mkdocs-ask-claude
cd mkdocs-ask-claude

# Create venv
uv venv
source .venv/bin/activate

# Install in editable mode with all dev dependencies
uv sync
# or
pip install -e "."
pip install pytest pytest-asyncio httpx fastapi uvicorn mkdocs-material
```

## Project structure

```
src/mkdocs_ask_claude/
├── __init__.py               # Public re-export of MkdocsAskClaudePlugin
├── py.typed                  # PEP 561 marker
├── assets/
│   ├── chat.js               # Widget — draggable button, panel, SSE streaming, markdown renderer
│   └── chat.css              # Widget styles + CSS custom properties
└── _internal/
    ├── plugin.py             # MkDocs plugin (on_config, on_post_build, on_page_context, on_post_page, on_startup)
    ├── config.py             # Plugin config schema (_PluginConfig)
    ├── server.py             # FastAPI chat backend (POST /chat, GET /health, ClaudeSDKClient sessions)
    ├── assets.py             # Asset registration + copy helpers
    ├── logger.py             # Plugin-namespaced logging adapter
    └── tools.py              # Reserved for custom Claude tool definitions (currently a stub)
```

## Running tests

```bash
pytest
```

All tests live in `tests/`:

| File | What it tests |
|---|---|
| `test_logger.py` | Logging adapter prefix, namespace, all levels |
| `test_assets.py` | CSS/JS registration, deduplication, file copy |
| `test_plugin.py` | All five MkDocs hooks including `on_post_page` config injection |
| `test_server.py` | FastAPI endpoints, SSE stream format, error handling, 422 validation |

## Architecture decisions

See [Architecture](reference/architecture.md) for how the modules collaborate.

Key decisions:

- **No custom Claude tools** — Claude uses its built-in `Bash` (curl), `WebFetch`, and `WebSearch` to read docs. This avoids maintaining custom tool definitions.
- **Docs read from disk, not HTTP** — the backend reads `site/llms.txt` and `site/llms-full.txt` directly from the filesystem and embeds the index in Claude's system prompt. Claude never needs to make an HTTP request to discover the page list.
- **Per-session asyncio worker tasks** — each browser session gets a dedicated asyncio `Task` that owns one `ClaudeSDKClient` for its lifetime. HTTP handlers communicate with the worker via asyncio queues, ensuring the SDK client is always used from the task that called `connect()`.
- **`on_startup` for server launch** — `on_serve` is not reliably called in MkDocs 1.6; `on_startup(command='serve')` fires before the build and is always triggered.
- **`on_post_page` for config injection** — injects `window.__CLAUDE_CHAT_CONFIG__` directly into each page's HTML before `</body>`, so no theme template override is required.
- **`fetch` + `ReadableStream` for SSE** — the backend uses `POST /chat`, so `EventSource` (GET-only) cannot be used. `fetch` with a `ReadableStream` reader handles the SSE protocol manually.
- **Pointer Events API for drag** — unified mouse + touch handling in one set of event listeners, with `setPointerCapture` for reliable drag tracking.

## Making changes

### Modifying the widget

Edit `src/mkdocs_ask_claude/assets/chat.js` and `chat.css` directly — no build step needed. Reload the browser after saving (the files are re-copied on every build cycle during `mkdocs serve`).

### Modifying the plugin

Edit files in `src/mkdocs_ask_claude/_internal/`. Since the package is installed in editable mode, restart `mkdocs serve` to pick up changes.

### Modifying the chat backend

Edit `src/mkdocs_ask_claude/_internal/server.py`. Restart `mkdocs serve` to reload (the backend starts fresh each time `on_startup` fires).

## Code style

- Python: follow the existing style (type hints everywhere, Google docstrings, `from __future__ import annotations`)
- JavaScript: vanilla ES2020+, no transpiler, no external libraries
- CSS: use the existing `--cc-*` custom properties for all colors
