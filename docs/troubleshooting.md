# Troubleshooting

## Chat button does not appear

**Symptom**: The floating chat button is missing from every page.

**Check 1 — plugin is enabled**

```yaml
plugins:
  - claude-chat:
      enabled: true   # default — make sure it's not set to false
```

**Check 2 — assets were copied**

Look for these lines in `mkdocs serve` output:

```
INFO    -  claude-chat: starting chat backend on http://localhost:8001
```

If missing, the `on_startup` hook did not fire. Make sure you are running `mkdocs serve`, not `mkdocs build`.

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

If another process is already on port 8001, kill it or configure a different port.

**Check 3 — stale process from a previous run**

If you restarted `mkdocs serve` but an old backend is still holding port 8001:

```bash
kill $(lsof -ti:8001)
```

Then restart `mkdocs serve`.

---

## Chatbot answers from general knowledge instead of your docs

**Symptom**: Claude says "I don't have specific documentation about..." or answers incorrectly.

**Cause**: `llms-full.txt` / `llms.txt` is missing from the built site, so the backend has no docs to embed in the system prompt.

The backend reads docs **directly from disk** (no HTTP involved). Every build writes the file; every new chat session reads it fresh.

**Check 1 — verify the file exists after build**

```bash
ls site/llms-full.txt   # preferred (all docs in one file)
ls site/llms.txt        # fallback index
```

If neither file exists, the `mkdocs-llmstxt` plugin is not installed or not configured.

Install it:

```bash
pip install mkdocs-llmstxt
```

Add to `mkdocs.yml`:

```yaml
plugins:
  - llmstxt:
      full_output: llms-full.txt   # single file with all docs — recommended
      sections:
        Docs:
          - "**"
  - claude-chat
```

**Check 2 — trigger a fresh chat session**

Docs are embedded when a **new** session starts. Reload the page (new session ID) and ask your question again.

**Check 3 — check backend logs**

Run `mkdocs serve` and look for:

```
DEBUG   - claude-chat: loaded docs (NNNNN chars) from /path/to/site/llms-full.txt
```

If you see a warning instead (`no llms-full.txt or llms.txt found`), the file is missing from the build output.

---

## Claude cannot fetch local URLs (`ECONNREFUSED`)

**Symptom**: Claude explicitly says it cannot connect to `127.0.0.1:8000`.

**Cause**: Claude runs in a sandboxed subprocess that cannot reach `localhost`. This is expected — the **plugin backend reads docs directly from the built site directory** on disk and injects them into Claude's system prompt, so Claude never needs localhost access.

If you see this error, the docs content is already in Claude's context (embedded in the system prompt). The error appears only if Claude tries to fetch more pages on its own, which it should not need to do.

**Check** that `llms-full.txt` or `llms.txt` is present in your site output directory after build:

```bash
ls $(mkdocs get-config site_dir)/llms-full.txt 2>/dev/null || echo "not found"
# or:
ls site/llms-full.txt
```

If neither file exists, the `mkdocs-llmstxt` plugin is not installed or not configured. See [Chatbot answers from general knowledge](#chatbot-answers-from-general-knowledge-instead-of-your-docs).

---

## Backend crashes on startup

**Symptom**: `mkdocs serve` shows `claude-chat: chat backend crashed: ...`.

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

This is a known MkDocs 1.6 issue — `on_serve` is registered but silently never called in some configurations. The plugin uses `on_startup(command='serve')` instead, which fires reliably.

No action needed — this is already handled internally.

---

## Widget panel does not push page content aside

**Symptom**: The chat panel overlaps the page content instead of shifting it.

**Cause**: Your theme applies `overflow: hidden` or `position: fixed` to the body or main container, which prevents `margin-right` from working.

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

If `site_url` in `mkdocs.yml` has a path (e.g. `https://org.github.io/my-project`), the plugin derives:

```
http://127.0.0.1:8000/my-project/llms.txt   # during serve
https://org.github.io/my-project/llms.txt   # during build
```

If your setup differs, set it explicitly:

```yaml
plugins:
  - claude-chat:
      llmstxt_url: http://127.0.0.1:8000/llms.txt
```
