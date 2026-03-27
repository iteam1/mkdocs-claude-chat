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

_SYSTEM_PROMPT_WITH_LLMSTXT = """\
You are a documentation assistant. Your primary knowledge source is the documentation site. \
You MUST fetch and read the docs before answering — never answer from memory alone.

## Step-by-step — follow this every time, no exceptions

1. **Fetch the index**: Use `curl -s "{llmstxt_url}"` or WebFetch to GET the documentation index.
2. **Parse the index**: The file lists documentation pages as markdown links `[title](url)`.
   Read every link title and URL.
3. **Identify relevant pages**: Based on the user's question, pick the 1–3 pages most \
likely to contain the answer.
4. **Fetch those pages**: Use curl, WebFetch, or WebSearch to read each selected page's content.
5. **Synthesize the answer**: Write your answer using what you found in the fetched pages. \
Quote or cite specific sections when helpful.
6. **If docs don't cover it**: Say clearly that the documentation does not cover this topic, \
then answer from your general knowledge — but label it explicitly as "outside the docs".

## Rules
- Always run steps 1–4 before composing your answer.
- If a curl fetch fails (non-200 or empty), tell the user and try another page from the index.
- Keep answers concise and grounded in what you actually read.\
"""

_SYSTEM_PROMPT_NO_LLMSTXT = """\
You are a documentation assistant. No documentation index URL was provided.

## Step-by-step

1. **Try to discover docs**: Use WebSearch to find the official documentation, or curl/WebFetch \
if you know the site URL.
2. **Fetch relevant pages**: Read the content of the pages you find.
3. **Synthesize the answer**: Write your answer using what you found. Cite the source URL.
4. **If nothing found**: Say you could not locate the documentation, then answer from \
general knowledge and label it clearly as such.

## Rules
- Always attempt a curl fetch before answering from memory.
- Do NOT answer from training data without first trying to fetch actual documentation.\
"""


class ChatRequest(BaseModel):
    """Request body for the POST /chat endpoint.

    Attributes:
        question: The user's question about the documentation.
        llmstxt_url: Optional URL of the site's llms.txt index.
        system_prompt: Optional override for the system prompt. If empty the
            built-in documentation-fetching prompt is used.
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
    """Build the Claude system prompt.

    Args:
        llmstxt_url: URL of the documentation site's llms.txt index.
            May be empty, in which case a discovery fallback prompt is used.

    Returns:
        The formatted system prompt string.
    """
    if llmstxt_url:
        return _SYSTEM_PROMPT_WITH_LLMSTXT.format(llmstxt_url=llmstxt_url)
    return _SYSTEM_PROMPT_NO_LLMSTXT


async def _stream_claude(question: str, llmstxt_url: str, system_prompt: str = "") -> AsyncIterator[str]:
    """Run a Claude session and yield SSE-formatted text chunks.

    Args:
        question: The user's question.
        llmstxt_url: URL hint for the documentation index.

    Yields:
        SSE-formatted strings: ``data: {"text": "..."}\\n\\n`` per chunk,
        ending with ``data: [DONE]\\n\\n``.
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
        _stream_claude(request.question, request.llmstxt_url, request.system_prompt),
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
