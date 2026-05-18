"""tailscale-ollama-expose: FastAPI reverse proxy exposing local Ollama over Tailscale."""

__version__ = "0.1.0"

from ollama_expose.config import Settings
from ollama_expose.server import create_app

__all__ = ["Settings", "create_app", "__version__"]
