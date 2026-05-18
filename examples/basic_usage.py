"""Basic usage example for tailscale-ollama-expose."""

from ollama_expose.config import Settings
from ollama_expose.server import create_app
import uvicorn

settings = Settings()
app = create_app(settings)

if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
