"""Tests for the chat server FastAPI application."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

import mkdocs_claude_chat._internal.server as srv
from mkdocs_claude_chat._internal.server import _build_system_prompt, app


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
# POST /chat — SSE stream (mocking _stream_claude)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_returns_sse_content_type() -> None:
    async def _mock(*args: object, **kwargs: object) -> AsyncIterator[str]:
        yield f"data: {json.dumps({'text': 'Hi'})}\n\n"
        yield "data: [DONE]\n\n"

    with patch("mkdocs_claude_chat._internal.server._stream_claude", _mock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "hi"})

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_chat_stream_contains_text_chunks() -> None:
    async def _mock(*args: object, **kwargs: object) -> AsyncIterator[str]:
        yield f"data: {json.dumps({'text': 'Hello world'})}\n\n"
        yield "data: [DONE]\n\n"

    with patch("mkdocs_claude_chat._internal.server._stream_claude", _mock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "hi"})

    lines = [l for l in response.text.splitlines() if l.startswith("data: ")]
    chunks = [json.loads(l[6:]) for l in lines if l != "data: [DONE]"]
    assert any(c.get("text") == "Hello world" for c in chunks)


@pytest.mark.asyncio
async def test_chat_stream_ends_with_done() -> None:
    async def _mock(*args: object, **kwargs: object) -> AsyncIterator[str]:
        yield f"data: {json.dumps({'text': 'answer'})}\n\n"
        yield "data: [DONE]\n\n"

    with patch("mkdocs_claude_chat._internal.server._stream_claude", _mock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "hi"})

    assert "data: [DONE]" in response.text


@pytest.mark.asyncio
async def test_chat_error_event_format() -> None:
    async def _mock(*args: object, **kwargs: object) -> AsyncIterator[str]:
        yield f"data: {json.dumps({'error': 'boom'})}\n\n"
        yield "data: [DONE]\n\n"

    with patch("mkdocs_claude_chat._internal.server._stream_claude", _mock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "fail"})

    data_lines = [l for l in response.text.splitlines() if l.startswith("data: ")]
    assert any('"error"' in l for l in data_lines)
    assert data_lines[-1] == "data: [DONE]"


@pytest.mark.asyncio
async def test_chat_tool_call_event_forwarded() -> None:
    tc = {"id": "t1", "name": "Bash", "command": "curl -s http://example.com/index.md"}

    async def _mock(*args: object, **kwargs: object) -> AsyncIterator[str]:
        yield f"data: {json.dumps({'tool_call': tc})}\n\n"
        yield "data: [DONE]\n\n"

    with patch("mkdocs_claude_chat._internal.server._stream_claude", _mock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/chat", json={"question": "hi"})

    data_lines = [l for l in response.text.splitlines() if l.startswith("data: ")]
    assert any('"tool_call"' in l for l in data_lines)


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


def test_system_prompt_custom_prompt_returned_as_is() -> None:
    custom = "You are a pirate assistant."
    assert _build_system_prompt(custom) == custom


def test_system_prompt_no_docs_fallback_when_no_site_dir() -> None:
    original = srv._site_dir
    srv._site_dir = ""
    try:
        prompt = _build_system_prompt("")
        assert "No documentation index" in prompt
    finally:
        srv._site_dir = original


def test_system_prompt_embeds_index_when_llms_txt_exists(tmp_path: "Path") -> None:  # type: ignore[name-defined]  # noqa: F821
    from pathlib import Path

    llms = tmp_path / "llms.txt"
    llms.write_text("# Docs\n- [Guide](http://localhost:8000/guide/)\n", encoding="utf-8")

    original = srv._site_dir
    srv._site_dir = str(tmp_path)
    try:
        prompt = _build_system_prompt("")
        assert "Guide" in prompt
        assert "No documentation index" not in prompt
    finally:
        srv._site_dir = original


# ---------------------------------------------------------------------------
# configure() — runtime settings
# ---------------------------------------------------------------------------


def test_configure_updates_globals() -> None:
    srv.configure(
        "/tmp/site",
        "http://localhost:8000/llms.txt",
        backend_port=9999,
        session_ttl=600,
        max_sessions=3,
    )
    assert srv._site_dir == "/tmp/site"
    assert srv._backend_port == 9999
    assert srv._session_ttl == 600
    assert srv._max_sessions == 3
    # restore defaults
    srv.configure("", "", backend_port=8001, session_ttl=7200, max_sessions=10)
