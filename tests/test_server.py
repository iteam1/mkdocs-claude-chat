"""Tests for the chat server FastAPI application."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from mkdocs_claude_chat._internal.server import _build_system_prompt, app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_async_iter(*messages: object) -> AsyncIterator[object]:
    """Yield objects as an async iterator."""
    for msg in messages:
        yield msg


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_returns_200() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /chat — SSE stream
# ---------------------------------------------------------------------------


def _make_assistant_message(text: str) -> object:
    """Build a minimal AssistantMessage-like object with a TextBlock."""
    from claude_agent_sdk import AssistantMessage, TextBlock

    block = TextBlock(text=text)
    return AssistantMessage(content=[block], model="claude-test")


@pytest.mark.asyncio
async def test_chat_returns_sse_content_type() -> None:
    msg = _make_assistant_message("Hello!")

    with patch(
        "mkdocs_claude_chat._internal.server.query",
        return_value=_make_async_iter(msg),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "hi"})

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_chat_stream_contains_text_chunks() -> None:
    msg = _make_assistant_message("Hello world")

    with patch(
        "mkdocs_claude_chat._internal.server.query",
        return_value=_make_async_iter(msg),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "hi"})

    lines = [line for line in response.text.splitlines() if line.startswith("data: ")]
    text_chunks = [json.loads(line[6:]) for line in lines if line != "data: [DONE]"]
    assert any("text" in chunk for chunk in text_chunks)
    assert any(chunk.get("text") == "Hello world" for chunk in text_chunks)


@pytest.mark.asyncio
async def test_chat_stream_ends_with_done() -> None:
    msg = _make_assistant_message("answer")

    with patch(
        "mkdocs_claude_chat._internal.server.query",
        return_value=_make_async_iter(msg),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "hi"})

    assert "data: [DONE]" in response.text


@pytest.mark.asyncio
async def test_chat_error_yields_error_then_done() -> None:
    async def _raise() -> AsyncIterator[object]:
        raise RuntimeError("boom")
        yield  # make it a generator

    with patch(
        "mkdocs_claude_chat._internal.server.query",
        side_effect=RuntimeError("boom"),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "fail"})

    lines = response.text.splitlines()
    data_lines = [l for l in lines if l.startswith("data: ")]
    assert any('"error"' in l for l in data_lines)
    assert data_lines[-1] == "data: [DONE]"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_missing_question_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_missing_body_returns_422() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# System prompt building
# ---------------------------------------------------------------------------


def test_system_prompt_with_llmstxt_url() -> None:
    prompt = _build_system_prompt("https://example.com/llms.txt")
    assert "https://example.com/llms.txt" in prompt
    assert "No documentation index" not in prompt


def test_system_prompt_without_llmstxt_url() -> None:
    prompt = _build_system_prompt("")
    assert "No documentation index URL provided" in prompt
    assert "<unknown>" in prompt
