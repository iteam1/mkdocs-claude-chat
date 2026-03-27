# Installation

## Prerequisites

Before installing the plugin, make sure you have:

- **Python 3.10+**
- **MkDocs 1.5+** (`pip install mkdocs`)
- **Claude CLI** installed and authenticated

### Install the Claude CLI

The plugin uses the `claude` CLI under the hood. Install it from [claude.ai/code](https://claude.ai/code) and authenticate:

```bash
claude login
claude --version   # confirm it works
```

## Install the plugin

```bash
pip install mkdocs-claude-chat
```

Or with `uv`:

```bash
uv add mkdocs-claude-chat
```

## Add to mkdocs.yml

```yaml
plugins:
  - search
  - claude-chat
```

That's the minimum configuration. See [Configuration](../configuration.md) for all available options.

## Optional: add llms.txt support

Install [`mkdocs-llmstxt`](https://github.com/pawamoy/mkdocs-llmstxt) to generate an `llms.txt` index for your site. Claude will use it to find the most relevant sections before answering:

```bash
pip install mkdocs-llmstxt
```

```yaml
plugins:
  - search
  - llmstxt
  - claude-chat
```

When `llmstxt` is present, Claude automatically discovers it at `<site_url>/llms.txt`. No extra config needed.

## Verify

```bash
mkdocs serve
```

You should see in the terminal:

```
INFO    -  claude-chat: starting chat backend on http://localhost:8001
INFO    -  Building documentation...
INFO    -  Serving on http://127.0.0.1:8000/
```

Open your browser — a chat button appears at the bottom-right corner.
