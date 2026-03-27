"""Chat backend using ClaudeSDKClient."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

from mkdocs_claude_chat._internal.logger import get_logger

_logger = get_logger(__name__)

_SYSTEM_PROMPT_TEMPLATE = """\
You are a helpful assistant answering questions about a documentation site.

{llmstxt_hint}

1. Check {llmstxt_url_display} — if it exists, use it as the index (see https://llmstxt.org/)
2. Traverse links in llms.txt with curl/WebFetch to find relevant sections
3. If no llms.txt, fall back to WebFetch or WebSearch

Be concise and accurate. Quote or reference specific sections when possible.\
"""


class ChatRequest(BaseModel):
    """Request body for the POST /chat endpoint.

    Attributes:
        question: The user's question about the documentation.
        llmstxt_url: Optional URL of the site's llms.txt index. Passed as a
            hint to Claude so it knows where to find the documentation index.
    """

    question: str
    llmstxt_url: str = ""


app = FastAPI(title="mkdocs-claude-chat server", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _build_system_prompt(llmstxt_url: str) -> str:
    """Build the Claude system prompt with an llms.txt hint.

    Args:
        llmstxt_url: URL of the documentation site's llms.txt index.
            May be empty, in which case a fallback message is used.

    Returns:
        The formatted system prompt string.
    """
    if llmstxt_url:
        hint = f"The documentation index is available at: {llmstxt_url}"
        display = llmstxt_url
    else:
        hint = "No documentation index URL provided — use WebFetch or WebSearch."
        display = "<unknown>"
    return _SYSTEM_PROMPT_TEMPLATE.format(
        llmstxt_hint=hint,
        llmstxt_url_display=display,
    )


async def _stream_claude(question: str, llmstxt_url: str) -> AsyncIterator[str]:
    """Run a Claude session and yield SSE-formatted text chunks.

    Args:
        question: The user's question.
        llmstxt_url: URL hint for the documentation index.

    Yields:
        SSE-formatted strings: ``data: {"text": "..."}\\n\\n`` per chunk,
        ending with ``data: [DONE]\\n\\n``.
    """
    system_prompt = _build_system_prompt(llmstxt_url)
    options = ClaudeAgentOptions(system_prompt=system_prompt)
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
    """Liveness check endpoint.

    Returns:
        A JSON object confirming the server is running.
    """
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream a Claude answer to the user's question.

    Args:
        request: The chat request containing the question and optional llmstxt_url.

    Returns:
        A streaming SSE response. Each event contains a text chunk; the stream
        ends with ``data: [DONE]``.
    """
    _logger.debug("chat request: question=%r, llmstxt_url=%r", request.question, request.llmstxt_url)
    return StreamingResponse(
        _stream_claude(request.question, request.llmstxt_url),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def run(port: int = 8001) -> None:
    """Start the chat server on the given port.

    Intended to be called by the MkDocs plugin during ``on_serve``. Blocks
    until the server is stopped.

    Args:
        port: TCP port to listen on. Defaults to ``8001``.
    """
    _logger.info("starting chat server on port %d", port)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
