# Contributing

## Development setup

```bash
git clone https://github.com/your-org/mkdocs-claude-chat
cd mkdocs-claude-chat

# Create venv
uv venv
source .venv/bin/activate

# Install in editable mode with all dev dependencies
uv pip install -e ".[dev]"
# or
pip install -e "."
pip install pytest pytest-asyncio httpx fastapi uvicorn mkdocs-material
```

## Project structure

```
src/mkdocs_claude_chat/
├── __init__.py               # Public re-export of MkdocsClaudeChatPlugin
├── py.typed                  # PEP 561 marker
├── assets/
│   ├── chat.js               # Widget — draggable button, panel, SSE streaming
│   └── chat.css              # Widget styles + CSS custom properties
└── _internal/
    ├── plugin.py             # MkDocs plugin (on_config, on_post_build, on_page_context, on_startup)
    ├── config.py             # Plugin config schema (_PluginConfig)
    ├── server.py             # FastAPI chat backend (POST /chat, GET /health)
    ├── assets.py             # Asset registration + copy helpers
    └── logger.py             # Plugin-namespaced logging adapter
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
| `test_plugin.py` | All four MkDocs hooks including `on_post_page` config injection |
| `test_server.py` | FastAPI endpoints, SSE stream format, error handling, 422 validation |

## Architecture decisions

See [Architecture](reference/architecture.md) for how the modules collaborate.

Key decisions:

- **No custom Claude tools** — Claude uses its built-in `WebFetch`, `curl`, and `WebSearch` to read docs. This avoids maintaining custom tool definitions.
- **`on_startup` for server launch** — `on_serve` is not reliably called in MkDocs 1.6; `on_startup(command='serve')` fires before the build and is always triggered.
- **`on_post_page` for config injection** — Injects `window.__CLAUDE_CHAT_CONFIG__` directly into each page's HTML before `</body>`, so no theme template override is required.
- **`fetch` + `ReadableStream` for SSE** — The backend uses `POST /chat`, so `EventSource` (GET-only) can't be used. `fetch` with a `ReadableStream` reader handles the SSE protocol manually.
- **Pointer Events API for drag** — Unified mouse + touch handling in one set of event listeners, with `setPointerCapture` for reliable drag tracking.

## Making changes

### Modifying the widget

Edit `src/mkdocs_claude_chat/assets/chat.js` and `chat.css` directly — no build step needed. Reload the browser after saving.

### Modifying the plugin

Edit files in `src/mkdocs_claude_chat/_internal/`. Since the package is installed in editable mode, restart `mkdocs serve` to pick up changes.

### Modifying the chat backend

Edit `src/mkdocs_claude_chat/_internal/server.py`. Restart `mkdocs serve` to reload (the backend starts fresh each time).

## Code style

- Python: follow the existing style (type hints everywhere, Google docstrings, `from __future__ import annotations`)
- JavaScript: vanilla ES2020+, no transpiler, no external libraries
- CSS: use the existing `--cc-*` custom properties for all colors
