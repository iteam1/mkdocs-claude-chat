# Troubleshooting

## Chat button does not appear

**Symptom**: The floating chat button is missing from every page.

**Check 1 — plugin is enabled**

```yaml
plugins:
  - ask-claude:
      enabled: true   # default — make sure it's not set to false
```

**Check 2 — backend started**

Look for this line in `mkdocs serve` output:

```
INFO    -  ask-claude: starting chat backend on http://localhost:8001
```

If missing, the `on_startup` hook did not fire. Make sure you are running `mkdocs serve`, not `mkdocs build` — the backend only starts during `serve`.

---

## "Chat unavailable — Failed to fetch"

**Symptom**: Clicking the chat button and sending a message shows a red error bubble.

**Cause**: The browser cannot reach the FastAPI backend on port 8001.

**Check 1 — backend is running**

```bash
curl http://localhost:8001/health
# expected: {"status":"ok"}
```

**Check 2 — port conflict**

```bash
ss -tlnp | grep 8001
```

If another process is already on port 8001, kill it or configure a different port:

```yaml
plugins:
  - ask-claude:
      backend_port: 8080
```

**Check 3 — stale process from a previous run**

If you restarted `mkdocs serve` but an old backend is still holding the port:

```bash
kill $(lsof -ti:8001)
```

Then restart `mkdocs serve`.

---

## Chatbot answers from general knowledge instead of your docs

**Symptom**: Claude says "I don't have specific documentation about..." or answers incorrectly.

**Cause**: `llms.txt` is missing from the built site directory, so the backend has nothing to embed in the system prompt.

The backend reads docs **directly from disk** (`site/llms.txt` and optionally `site/llms-full.txt`). Every build writes these files; every new session reads them fresh.

**Check 1 — verify the file exists after build**

```bash
ls site/llms.txt         # index with page URLs and descriptions
ls site/llms-full.txt    # optional: single file with all docs merged
```

If neither file exists, `mkdocs-llmstxt` is not installed or not configured.

Install it:

```bash
pip install mkdocs-llmstxt
```

Add to `mkdocs.yml` (before `ask-claude`):

```yaml
plugins:
  - llmstxt:
      full_output: llms-full.txt   # single file with all docs — recommended
      sections:
        Docs:
          - "**"
  - ask-claude
```

**Check 2 — trigger a fresh chat session**

Docs are embedded when a **new** session starts. The close button in the chat panel clears the session. Alternatively, open a new tab — each tab gets a fresh session ID.

**Check 3 — check backend logs**

Run `mkdocs serve` and look for:

```
DEBUG   - ask-claude: system prompt built (NNNNN chars)
```

A very short prompt (a few hundred chars) means the docs index was not found.

---

## Backend crashes on startup

**Symptom**: `mkdocs serve` shows `ask-claude: chat backend crashed: ...`.

**Check 1 — missing dependencies**

```bash
pip install fastapi uvicorn claude-agent-sdk anyio
```

**Check 2 — Claude CLI not authenticated**

```bash
claude --version   # must succeed
claude login       # re-authenticate if needed
```

---

## `on_serve` hook never fires (MkDocs 1.6)

This is a known MkDocs 1.6 issue — `on_serve` is registered but silently never called in some configurations. The plugin uses `on_startup(command='serve')` instead, which fires reliably before the first build.

No action needed — this is already handled internally.

---

## Widget panel does not push page content aside

**Symptom**: The chat panel overlaps the page content instead of shifting it left.

**Cause**: Your theme applies `overflow: hidden` or `position: fixed` to the `body` or main container, which prevents `margin-right` from working.

**Fix**: Add extra CSS to your site:

```css
/* docs/stylesheets/extra.css */
body {
  overflow-x: visible !important;
}
```

```yaml
extra_css:
  - stylesheets/extra.css
```

---

## Panel resize does not work on mobile

By design — the resize handle is hidden on screens narrower than 480px and the panel goes full-width. This is intentional to avoid awkward drag targets on touch screens.

---

## `llmstxt_url` auto-detection is wrong

If `site_url` in `mkdocs.yml` has a sub-path (e.g. `https://org.github.io/my-project`), the plugin derives:

```
http://127.0.0.1:8000/my-project/llms.txt   # during serve
https://org.github.io/my-project/llms.txt   # during build
```

If your setup differs, set it explicitly:

```yaml
plugins:
  - ask-claude:
      llmstxt_url: http://127.0.0.1:8000/llms.txt
```

Note: this URL is only used as a reference in the system prompt's fallback instructions. The backend always reads `llms.txt` directly from disk.
