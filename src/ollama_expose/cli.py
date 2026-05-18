from __future__ import annotations

import argparse

import uvicorn

from ollama_expose.config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Expose local Ollama over the network via a FastAPI reverse proxy.",
    )
    parser.add_argument("--host", default=None, help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="Bind port (default: 11434)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    settings = Settings()
    host = args.host or settings.host
    port = args.port or settings.port

    uvicorn.run(
        "ollama_expose.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
