from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from ollama_expose.config import Settings
from ollama_expose.server import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ollama_url="http://localhost:11434",
        auth_token="test-secret",
        timeout=10.0,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings)
    return TestClient(app)


def test_health_ok(client: TestClient) -> None:
    mock_response = httpx.Response(
        200,
        json={"models": [{"name": "llama3:8b"}, {"name": "mistral:7b"}]},
    )

    with patch("ollama_expose.server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        resp = client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "llama3:8b" in data["models"]


def test_health_connection_refused(client: TestClient) -> None:
    with patch("ollama_expose.server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client_cls.return_value = mock_client

        resp = client.get("/health")

    assert resp.status_code == 502
    assert "Cannot connect" in resp.json()["detail"]


def test_health_timeout(client: TestClient) -> None:
    with patch("ollama_expose.server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
        mock_client_cls.return_value = mock_client

        resp = client.get("/health")

    assert resp.status_code == 504
    assert "timed out" in resp.json()["detail"]


def test_proxy_no_auth(client: TestClient) -> None:
    settings_no_auth = Settings(ollama_url="http://localhost:11434", auth_token="")
    app = create_app(settings_no_auth)
    test_client = TestClient(app)

    mock_response = httpx.Response(200, json={"model": "llama3:8b", "response": "hello"})

    with patch("ollama_expose.server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        resp = test_client.post("/api/generate", json={"model": "llama3:8b", "prompt": "hi"})

    assert resp.status_code == 200
    assert resp.json()["response"] == "hello"


def test_proxy_auth_valid(client: TestClient) -> None:
    mock_response = httpx.Response(200, json={"model": "llama3:8b", "response": "hello"})

    with patch("ollama_expose.server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        resp = client.post(
            "/api/generate",
            json={"model": "llama3:8b", "prompt": "hi"},
            headers={"Authorization": "Bearer test-secret"},
        )

    assert resp.status_code == 200


def test_proxy_auth_missing(client: TestClient) -> None:
    resp = client.post("/api/generate", json={"model": "llama3:8b", "prompt": "hi"})
    assert resp.status_code == 401


def test_proxy_auth_invalid(client: TestClient) -> None:
    resp = client.post(
        "/api/generate",
        json={"model": "llama3:8b", "prompt": "hi"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert resp.status_code == 401


def test_proxy_connection_error(client: TestClient) -> None:
    with patch("ollama_expose.server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.request = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client_cls.return_value = mock_client

        resp = client.post(
            "/api/generate",
            json={"model": "llama3:8b", "prompt": "hi"},
            headers={"Authorization": "Bearer test-secret"},
        )

    assert resp.status_code == 502


def test_proxy_cors_headers(client: TestClient) -> None:
    resp = client.options("/api/generate")
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "*"


def test_proxy_timeout(client: TestClient) -> None:
    with patch("ollama_expose.server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client_cls.return_value = mock_client

        resp = client.post(
            "/api/generate",
            json={"model": "llama3:8b", "prompt": "hi"},
            headers={"Authorization": "Bearer test-secret"},
        )

    assert resp.status_code == 504


def test_proxy_streaming(client: TestClient) -> None:
    settings_no_auth = Settings(ollama_url="http://localhost:11434", auth_token="", timeout=10.0)
    app = create_app(settings_no_auth)
    test_client = TestClient(app)

    sse_data = [
        b'{"model":"llama3:8b","response":"hello","done":false}\n',
        b'{"model":"llama3:8b","response":" world","done":true}\n',
    ]

    async def fake_aiter_bytes():
        for chunk in sse_data:
            yield chunk

    mock_stream_resp = httpx.Response(
        200,
        stream=fake_aiter_bytes(),
        headers={"content-type": "text/event-stream"},
    )

    with patch("ollama_expose.server.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.build_request = lambda **kw: httpx.Request("POST", "http://fake")
        mock_stream = AsyncMock()
        mock_stream.status_code = 200
        mock_stream.headers = {"content-type": "text/event-stream"}
        mock_stream.aiter_bytes = fake_aiter_bytes
        mock_stream.aclose = AsyncMock()
        mock_client.send = AsyncMock(return_value=mock_stream)
        mock_client_cls.return_value = mock_client

        resp = test_client.post(
            "/api/generate",
            json={"model": "llama3:8b", "prompt": "hi", "stream": True},
        )

    assert resp.status_code == 200
    content = resp.text
    assert "hello" in content
    assert "world" in content
