from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    ollama_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434"),
    )
    auth_token: str = field(
        default_factory=lambda: os.getenv("OLLAMA_AUTH_TOKEN", ""),
    )
    timeout: float = field(
        default_factory=lambda: float(os.getenv("OLLAMA_TIMEOUT", "300")),
    )
    host: str = field(
        default_factory=lambda: os.getenv("OLLAMA_EXPOSE_HOST", "0.0.0.0"),
    )
    port: int = field(
        default_factory=lambda: int(os.getenv("OLLAMA_EXPOSE_PORT", "11434")),
    )

    @property
    def auth_enabled(self) -> bool:
        return bool(self.auth_token)
