"""Chat backend using ClaudeSDKClient for stateful multi-turn conversations.

Each browser session gets a dedicated asyncio background task that owns one
``ClaudeSDKClient`` for the lifetime of the session.  HTTP request coroutines
communicate with that task via asyncio queues, so the SDK client is always
used from the same async task that called ``connect()`` — satisfying the SDK
caveat about async-context isolation.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, TextBlock

from mkdocs_claude_chat._internal.logger import get_logger

_logger = get_logger(__name__)

# ── Server config (set by plugin after each build) ────────────────────────────
_site_dir: str = ""
_llmstxt_url: str = ""   # HTTP URL of llms.txt, e.g. http://127.0.0.1:8000/site/llms.txt


def configure(site_dir: str, llmstxt_url: str = "") -> None:
    """Tell the server where docs live and how to reach llms.txt over HTTP.

    Called by the MkDocs plugin after each build.

    Args:
        site_dir: Absolute path to the MkDocs build output directory.
            Used as the local file fallback when HTTP is unavailable.
        llmstxt_url: Full HTTP URL of ``llms.txt``, e.g.
            ``http://127.0.0.1:8000/my-site/llms.txt``.
            Claude uses this to traverse links via ``curl``.
    """
    global _site_dir, _llmstxt_url
    _site_dir = site_dir
    _llmstxt_url = llmstxt_url
    _logger.info("claude-chat: docs dir → %s  llmstxt → %s", site_dir, llmstxt_url)


# ── Docs loading (filesystem, not HTTP) ───────────────────────────────────────

def _read_llms_index() -> str:
    """Read ``llms.txt`` — the small documentation index listing available pages."""
    if not _site_dir:
        return ""
    path = Path(_site_dir) / "llms.txt"
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def _llms_full_path() -> Path | None:
    """Return the path to ``llms-full.txt`` if it exists."""
    if not _site_dir:
        return None
    p = Path(_site_dir) / "llms-full.txt"
    return p if p.exists() else None


# ── System prompts ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a documentation assistant.

## MANDATORY: Always look up the docs before answering any question

Use the following strategy in order — move to the next only if the previous fails:

**Option 1 — llmstxt.org protocol (preferred)**
curl -s {llmstxt_url}
→ Read the index, identify relevant pages, then fetch the .md version and grep:
curl -s <page_url_with_.md> | grep -i -A 30 "keyword"

**Option 2 — grep the full doc file over HTTP**
curl -s {llms_full_url} | grep -i -A 30 "keyword"

**Option 3 — grep the local file (if HTTP is unreachable)**
grep -i -A 30 "keyword" {llms_full_path}

Never skip all three. Never answer from memory alone — always fetch or grep first.

## Handling any URL the user gives you

When the user pastes a URL (with or without a `#section`):

1. Fetch `llms.txt` first (if not already done) — match the URL's path against the index
   to find the canonical `.md` link for that page.
2. Fetch the `.md` version of the page (clean Markdown, easier to grep than HTML):
   - trailing `/`  →  append `index.md`   (e.g. `.../quickstart/` → `.../quickstart/index.md`)
   - `.html` or no extension  →  swap for `index.md` at the same path
3. If the URL has a `#fragment`, use the fragment words as grep keywords to jump
   to the right section:
   curl -s <page.md_url> | grep -i -A 30 "fragment words"
4. If the path does not match anything in `llms.txt`, still try to fetch it as-is.

## After looking up the docs

- Answer based on what you found.
- Quote or reference the specific sections.
- If a topic is not in the docs after searching, say so clearly, \
then you may use general knowledge — label it as "(outside the docs)".\
"""

_SYSTEM_PROMPT_NO_DOCS = """\
You are a documentation assistant. No documentation index was found.

Try to help the user as best you can using your general knowledge, \
but make it clear you are not drawing from site-specific documentation.\
"""


def _build_system_prompt(custom_prompt: str = "") -> str:
    """Return the system prompt for a new conversation session.

    Claude is given the URL of ``llms.txt`` and instructed to use ``curl`` to
    traverse it per the llmstxt.org protocol — fetching only what it needs,
    so the context window is never pre-loaded with the full doc set.
    A local file fallback is included for when the HTTP server is unreachable.
    """
    if custom_prompt.strip():
        return custom_prompt.strip()

    if not _llmstxt_url and not _site_dir:
        return _SYSTEM_PROMPT_NO_DOCS

    full_path = _llms_full_path() or f"{_site_dir}/llms-full.txt"

    # Derive llms-full.txt HTTP URL from llms.txt URL (same base, different filename)
    llms_full_url = _llmstxt_url.rsplit("/", 1)[0] + "/llms-full.txt" if _llmstxt_url else "(unavailable)"

    prompt = _SYSTEM_PROMPT.format(
        llmstxt_url=_llmstxt_url or "(unavailable)",
        llms_full_url=llms_full_url,
        llms_full_path=full_path,
        site_dir=_site_dir or "(unavailable)",
    )
    _logger.debug("system prompt built (%d chars)", len(prompt))
    return prompt


# ── Per-session worker task ───────────────────────────────────────────────────
# ClaudeSDKClient must be used from the same async task that called connect().
# Each session gets a dedicated asyncio Task that owns one client instance.
# HTTP handlers communicate with the worker via asyncio Queues.
#
# Question queue items:  (question: str, reply_q: asyncio.Queue)
# Reply queue items:     ("text", str) | ("error", str) | ("done", None)

_SESSION_TTL = 7200   # seconds before an idle session is evicted
_MAX_SESSIONS = 10    # cap on simultaneous live Claude CLI processes


@dataclass
class _ChatSession:
    question_q: asyncio.Queue  # type: ignore[type-arg]
    task: asyncio.Task          # type: ignore[type-arg]
    last_used: float = field(default_factory=time.monotonic)


_sessions: dict[str, _ChatSession] = {}


async def _worker(question_q: asyncio.Queue, system_prompt: str) -> None:  # type: ignore[type-arg]
    """Background task: owns one ClaudeSDKClient and processes questions serially."""
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        permission_mode="bypassPermissions",
        allowed_tools=["Bash", "WebFetch", "WebSearch"],
    )
    try:
        async with ClaudeSDKClient(options) as client:
            while True:
                item: Any = await question_q.get()
                if item is None:  # shutdown signal
                    break
                question, reply_q = item
                try:
                    await client.query(question)
                    async for message in client.receive_response():
                        if isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, TextBlock) and block.text:
                                    await reply_q.put(("text", block.text))
                except Exception as exc:  # noqa: BLE001
                    _logger.error("worker error: %s", exc, exc_info=True)
                    await reply_q.put(("error", str(exc)))
                finally:
                    await reply_q.put(("done", None))
    except Exception as exc:  # noqa: BLE001
        _logger.error("worker crashed: %s", exc, exc_info=True)


async def _evict_expired() -> None:
    now = time.monotonic()
    expired = [sid for sid, s in list(_sessions.items()) if now - s.last_used > _SESSION_TTL]
    for sid in expired:
        session = _sessions.pop(sid, None)
        if session:
            await session.question_q.put(None)  # ask worker to stop
            _logger.debug("evicted expired session %s", sid)


async def _get_or_create_session(session_id: str, custom_prompt: str = "") -> _ChatSession:
    """Return an existing live session or spin up a new worker task."""
    await _evict_expired()

    existing = _sessions.get(session_id)
    if existing and not existing.task.done():
        existing.last_used = time.monotonic()
        return existing

    # Evict oldest if at capacity
    if len(_sessions) >= _MAX_SESSIONS:
        oldest_id = min(_sessions, key=lambda sid: _sessions[sid].last_used)
        old = _sessions.pop(oldest_id)
        await old.question_q.put(None)
        _logger.debug("evicted oldest session %s to make room", oldest_id)

    system_prompt = _build_system_prompt(custom_prompt)
    question_q: asyncio.Queue = asyncio.Queue()  # type: ignore[type-arg]
    task = asyncio.create_task(_worker(question_q, system_prompt))

    session = _ChatSession(question_q=question_q, task=task)
    _sessions[session_id] = session
    _logger.debug("created session %s (prompt: %d chars)", session_id, len(system_prompt))
    return session


# ── SSE streaming ──────────────────────────────────────────────────────────────

async def _stream_claude(
    question: str,
    system_prompt: str = "",
    session_id: str = "",
) -> AsyncIterator[str]:
    """Send *question* to Claude and yield SSE-formatted text chunks.

    When *session_id* is provided, the conversation is stateful — the same
    background worker (and its ``ClaudeSDKClient``) handles every turn, so
    Claude natively remembers the full conversation history.

    Yields:
        ``data: {"text": "..."}\\n\\n`` chunks, then ``data: [DONE]\\n\\n``.
    """
    reply_q: asyncio.Queue = asyncio.Queue()  # type: ignore[type-arg]

    try:
        if session_id:
            session = await _get_or_create_session(session_id, system_prompt)
            await session.question_q.put((question, reply_q))
            session.last_used = time.monotonic()
        else:
            # Stateless one-off: spin up a throw-away worker
            sp = _build_system_prompt(system_prompt)
            question_q: asyncio.Queue = asyncio.Queue()  # type: ignore[type-arg]
            task = asyncio.create_task(_worker(question_q, sp))
            await question_q.put((question, reply_q))
            await question_q.put(None)  # shut down after this one question
            try:
                while True:
                    kind, payload = await reply_q.get()
                    if kind == "done":
                        break
                    elif kind == "error":
                        yield f"data: {json.dumps({'error': payload})}\n\n"
                        break
                    elif kind == "text":
                        yield f"data: {json.dumps({'text': payload})}\n\n"
            finally:
                task.cancel()
            yield "data: [DONE]\n\n"
            return

        while True:
            kind, payload = await reply_q.get()
            if kind == "done":
                break
            elif kind == "error":
                yield f"data: {json.dumps({'error': payload})}\n\n"
                break
            elif kind == "text":
                yield f"data: {json.dumps({'text': payload})}\n\n"

    except Exception as exc:  # noqa: BLE001
        _logger.error("stream error: %s", exc, exc_info=True)
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    yield "data: [DONE]\n\n"


# ── FastAPI app ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for the POST /chat endpoint.

    Attributes:
        question: The user's question about the documentation.
        llmstxt_url: Ignored by the server (kept for client compatibility).
            The server reads docs directly from the filesystem.
        system_prompt: Optional override for the system prompt.
        session_id: Browser-generated ID to maintain conversation history
            across multiple messages in the same chat session.
    """

    question: str
    llmstxt_url: str = ""      # kept for backward compat — server ignores it
    system_prompt: str = ""
    session_id: str = ""


app = FastAPI(title="mkdocs-claude-chat server", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness check endpoint."""
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream a Claude answer to the user's question.

    Args:
        request: The chat request.

    Returns:
        A streaming SSE response ending with ``data: [DONE]``.
    """
    _logger.debug(
        "chat request: question=%r, session=%r",
        request.question,
        request.session_id,
    )
    return StreamingResponse(
        _stream_claude(request.question, request.system_prompt, request.session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def run(port: int = 8001) -> None:
    """Start the chat server on the given port.

    Args:
        port: TCP port to listen on. Defaults to ``8001``.
    """
    _logger.info("starting chat server on port %d", port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
