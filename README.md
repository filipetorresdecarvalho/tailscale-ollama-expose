# tailscale-ollama-expose

FastAPI reverse proxy that exposes a local Ollama instance over your Tailscale network.

## Architecture

```
┌─────────────────────┐         Tailscale VPN          ┌──────────────────────────┐
│   VPS / Client      │ ◄──────────────────────────────►│  Windows GPU Machine     │
│                     │                                 │                          │
│  httpx / curl /     │    ollama-expose (FastAPI)      │  ┌──────────────────┐    │
│  OpenWebUI          │ ─────► :11434 /api/* ──────────►│  │ Ollama :11434    │    │
│                     │                                 │  │ (localhost only) │    │
│                     │ ◄────── SSE / JSON ◄────────────│  └──────────────────┘    │
└─────────────────────┘                                 └──────────────────────────┘
```

## Install

```bash
pip install -e .
```

Or with dev dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

Start the server:

```bash
ollama-expose
```

Or with options:

```bash
ollama-expose --host 0.0.0.0 --port 11434
```

For development with auto-reload:

```bash
ollama-expose --reload
```

Then from any machine on your Tailscale network:

```bash
curl http://<tailscale-ip>:11434/health
curl http://<tailscale-ip>:11434/api/generate -d '{"model":"llama3:8b","prompt":"Hello"}'
```

## Configuration

All settings can be configured via environment variables:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Local Ollama endpoint URL |
| `OLLAMA_AUTH_TOKEN` | _(empty)_ | Bearer token for authentication (empty = no auth) |
| `OLLAMA_TIMEOUT` | `300` | Request timeout in seconds |
| `OLLAMA_EXPOSE_HOST` | `0.0.0.0` | Bind address |
| `OLLAMA_EXPOSE_PORT` | `11434` | Bind port |

## Features

- **Full API proxy** — Forwards all `/api/*` requests to local Ollama
- **Health check** — `GET /health` returns available models
- **Bearer token auth** — Optional authentication via `OLLAMA_AUTH_TOKEN`
- **CORS support** — Cross-origin requests allowed
- **Streaming (SSE)** — Passthrough streaming for `/api/generate` and `/api/chat` with `stream=true`
- **Error handling** — Returns 502 when Ollama is unreachable, 504 on timeout

## License

MIT
