# mkdocs-claude-chat

MkDocs plugin that adds a Claude-powered chatbot to your documentation site.

Claude reads **your docs**, not the internet — it uses `llms.txt` to know every page, fetches only what's relevant, and streams a synthesized answer back word-by-word.

## Installation

```bash
pip install git+https://github.com/iteam1/mkdocs-claude-chat
```

Or with `uv`:

```bash
uv pip install git+https://github.com/iteam1/mkdocs-claude-chat
```

For the best experience, also install [`mkdocs-llmstxt`](https://github.com/pawamoy/mkdocs-llmstxt) — it generates the `llms.txt` index that Claude uses as its docs map:

```bash
pip install mkdocs-llmstxt
```

## Requirements

- Python 3.10+
- MkDocs 1.5+
- **Claude Code CLI** installed and authenticated (`claude login`)

The plugin drives Claude through `claude-agent-sdk`. No API keys or environment variables needed beyond a logged-in `claude` CLI.

## Usage

```yaml
# mkdocs.yml
plugins:
  - search
  - llmstxt:
      full_output: llms-full.txt
      sections:
        Docs:
          - "**"
  - claude-chat
```

Run `mkdocs serve` — a chat button appears on every page.

## Configuration

| Option | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `true` | Disable the plugin entirely (useful for production builds) |
| `model` | str | `claude-sonnet-4-6` | Claude model for responses |
| `chat_title` | str | `Ask Claude` | Chat panel header text |
| `position` | str | `bottom-right` | Button position (`bottom-right` or `bottom-left`) |
| `llmstxt_url` | str | *(auto from site_url)* | Override the llms.txt URL |
| `system_prompt` | str | *(built-in)* | Replace the built-in system prompt |
| `backend_port` | int | `8001` | TCP port for the FastAPI chat server |
| `session_ttl` | int | `7200` | Seconds of inactivity before a session is evicted |
| `max_sessions` | int | `10` | Max simultaneous live Claude sessions |

## How it works

1. `mkdocs-llmstxt` builds `site/llms.txt` — a structured index of every page
2. `claude-chat` reads it from disk and embeds the full index in Claude's system prompt at session start
3. Claude knows your entire docs structure before the first question
4. For each question, Claude identifies all relevant pages, fetches them via `curl`, and synthesizes the answer
5. You can watch each fetch happen live — tool calls appear as collapsible blocks in the chat panel

## License

ISC
