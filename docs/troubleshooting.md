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

**Cause**: The `llmstxt_url` injected into the page is wrong — usually pointing to the remote `site_url` instead of the local dev server.

**Check 1 — hard-refresh the browser**

The browser may be showing a cached page with the old URL. Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac).

**Check 2 — inspect the injected config**

Open browser DevTools → Console and run:

```js
window.__CLAUDE_CHAT_CONFIG__
```

The `llmstxtUrl` should point to your local dev server:

```
http://127.0.0.1:8000/<your-site-path>/llms.txt
```

Not the remote `site_url`.

**Check 3 — verify llms.txt is being generated**

```bash
curl http://127.0.0.1:8000/<your-site-path>/llms.txt
```

If it returns HTML instead of Markdown, the `mkdocs-llmstxt` plugin is not installed or not configured.

Install it:

```bash
pip install mkdocs-llmstxt
```

Add to `mkdocs.yml`:

```yaml
plugins:
  - llmstxt:
      sections:
        Docs:
          - "**"
  - claude-chat
```

---

## Claude cannot fetch local URLs (`ECONNREFUSED`)

**Symptom**: Claude explicitly says it cannot connect to `127.0.0.1:8000`.

**Cause**: Claude runs in a sandboxed subprocess that cannot reach `localhost`. This is expected — the **plugin backend fetches the docs for Claude** automatically (server-side), so Claude should never need to reach `localhost` itself.

If you see this error, it means the backend pre-fetch failed and the docs content is not in Claude's context.

**Fix**: Check that `llms.txt` is accessible from the backend process:

```bash
curl http://127.0.0.1:8000/<your-site-path>/llms.txt
```

If that returns content, restart `mkdocs serve` and hard-refresh the browser.

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
