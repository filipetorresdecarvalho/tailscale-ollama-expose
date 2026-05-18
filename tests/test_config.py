from __future__ import annotations

import os

from ollama_expose.config import Settings


def test_default_settings() -> None:
    s = Settings()
    assert s.ollama_url == "http://localhost:11434"
    assert s.auth_token == ""
    assert s.timeout == 300.0
    assert s.host == "0.0.0.0"
    assert s.port == 11434
    assert not s.auth_enabled


def test_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_URL", "http://192.168.1.100:11434")
    monkeypatch.setenv("OLLAMA_AUTH_TOKEN", "mytoken")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "600")
    monkeypatch.setenv("OLLAMA_EXPOSE_HOST", "127.0.0.1")
    monkeypatch.setenv("OLLAMA_EXPOSE_PORT", "8080")

    s = Settings()
    assert s.ollama_url == "http://192.168.1.100:11434"
    assert s.auth_token == "mytoken"
    assert s.timeout == 600.0
    assert s.host == "127.0.0.1"
    assert s.port == 8080
    assert s.auth_enabled


def test_auth_enabled() -> None:
    s = Settings(auth_token="secret")
    assert s.auth_enabled

    s2 = Settings(auth_token="")
    assert not s2.auth_enabled
