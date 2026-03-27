"""Chat backend using ClaudeSDKClient."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections.abc import AsyncIterator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

from mkdocs_claude_chat._internal.logger import get_logger

_logger = get_logger(__name__)

# ── Docs cache ────────────────────────────────────────────────────────────────
# Keyed by llmstxt_url. Refreshed at most once every 15 seconds so hot-reloads
# are picked up quickly without hammering the dev server on every message.
_CACHE_TTL = 15  # seconds
_docs_cache: dict[str, tuple[float, str]] = {}  # url -> (timestamp, content)


def _fetch(url: str, timeout: int = 5) -> str:
    """Fetch a URL and return the response body as text. Returns '' on error."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        _logger.debug("fetch failed %s: %s", url, exc)
        return ""


def _base_url(llmstxt_url: str) -> str:
    """Return the base URL (everything before the filename)."""
    return llmstxt_url.rsplit("/", 1)[0] + "/"


def _load_docs(llmstxt_url: str) -> str:
    """Fetch and return documentation content for the given llms.txt URL.

    Strategy:
    1. Try ``<base>/llms-full.txt`` — a single file with all docs concatenated.
    2. Fall back: fetch ``llms.txt``, parse every markdown link, fetch each page.

    Results are cached for :data:`_CACHE_TTL` seconds.
    """
    now = time.monotonic()
    cached = _docs_cache.get(llmstxt_url)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]

    base = _base_url(llmstxt_url)
    full_txt_url = base + "llms-full.txt"
    content = _fetch(full_txt_url)

    if not content:
        # Fall back: fetch llms.txt index, then each linked page
        index = _fetch(llmstxt_url)
        if index:
            pages = [llmstxt_url]  # include the index itself
            for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", index):
                page_url = match.group(2)
                if not page_url.startswith("http"):
                    page_url = base + page_url.lstrip("/")
                pages.append(page_url)
            parts = [index]
            for page_url in pages[1:]:
                page = _fetch(page_url)
                if page:
                    parts.append(f"\n\n---\n<!-- source: {page_url} -->\n\n{page}")
            content = "\n".join(parts)

    _docs_cache[llmstxt_url] = (now, content)
    _logger.debug("loaded docs (%d chars) from %s", len(content), llmstxt_url)
    return content


# ── System prompts ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT_WITH_DOCS = """\
You are a documentation assistant. The full documentation content is provided below — \
use it as your primary knowledge source.

## Documentation

{docs_content}

---

## Instructions

- Answer based on the documentation above.
- Quote or reference specific sections when helpful.
- If the question is not covered in the docs, say so clearly, \
then you may supplement with general knowledge — label it as "(outside the docs)".
- Keep answers concise and accurate.\
"""

_SYSTEM_PROMPT_NO_DOCS = """\
You are a documentation assistant. No documentation content was found.

Try to help the user as best you can using your general knowledge, \
but make it clear you are not drawing from site-specific documentation.\
"""


class ChatRequest(BaseModel):
    """Request body for the POST /chat endpoint.

    Attributes:
        question: The user's question about the documentation.
        llmstxt_url: URL of the site's llms.txt index. The server fetches it
            directly so Claude does not need localhost access.
        system_prompt: Optional override for the system prompt.
    """

    question: str
    llmstxt_url: str = ""
    system_prompt: str = ""


app = FastAPI(title="mkdocs-claude-chat server", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _build_system_prompt(llmstxt_url: str) -> str:
    """Build the system prompt, pre-loading doc content from *llmstxt_url*.

    The server fetches the documentation itself (it has localhost access)
    and injects the content directly so Claude never needs network access.

    Args:
        llmstxt_url: URL of the site's llms.txt (or llms-full.txt base).

    Returns:
        Formatted system prompt string with docs embedded.
    """
    if not llmstxt_url:
        return _SYSTEM_PROMPT_NO_DOCS

    docs = _load_docs(llmstxt_url)
    if not docs:
        _logger.warning("could not load docs from %s — Claude will answer without context", llmstxt_url)
        return _SYSTEM_PROMPT_NO_DOCS

    return _SYSTEM_PROMPT_WITH_DOCS.format(docs_content=docs)


async def _stream_claude(question: str, llmstxt_url: str, system_prompt: str = "") -> AsyncIterator[str]:
    """Run a Claude session and yield SSE-formatted text chunks.

    Args:
        question: The user's question.
        llmstxt_url: URL of the docs index — fetched server-side and injected
            into the system prompt so Claude does not need localhost access.
        system_prompt: Optional caller-supplied prompt override.

    Yields:
        SSE strings: ``data: {"text": "..."}\\n\\n`` per chunk,
        then ``data: [DONE]\\n\\n``.
    """
    resolved_prompt = system_prompt.strip() or _build_system_prompt(llmstxt_url)
    options = ClaudeAgentOptions(
        system_prompt=resolved_prompt,
        permission_mode="bypassPermissions",
        allowed_tools=["Bash", "WebFetch", "WebSearch"],
    )
    try:
        async for message in query(prompt=question, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock) and block.text:
                        yield f"data: {json.dumps({'text': block.text})}\n\n"
    except Exception as exc:  # noqa: BLE001
        _logger.error("Claude session error: %s", exc)
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"
    yield "data: [DONE]\n\n"


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
    _logger.debug("chat request: question=%r, llmstxt_url=%r", request.question, request.llmstxt_url)
    return StreamingResponse(
        _stream_claude(request.question, request.llmstxt_url, request.system_prompt),
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
