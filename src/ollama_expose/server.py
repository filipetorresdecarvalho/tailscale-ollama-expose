from __future__ import annotations

import json
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from ollama_expose.config import Settings

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
}


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    app = FastAPI(title="Ollama Expose", version="0.1.0")
    router = APIRouter()

    @router.get("/health")
    async def health() -> JSONResponse:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.ollama_url}/api/tags")
                data = resp.json()
                return JSONResponse(
                    content={
                        "status": "ok",
                        "models": [m["name"] for m in data.get("models", [])],
                    },
                    headers=CORS_HEADERS,
                )
        except httpx.ConnectError:
            return JSONResponse(
                status_code=502,
                content={
                    "status": "error",
                    "detail": f"Cannot connect to Ollama at {settings.ollama_url}",
                },
                headers=CORS_HEADERS,
            )
        except httpx.TimeoutException:
            return JSONResponse(
                status_code=504,
                content={
                    "status": "error",
                    "detail": f"Ollama health check timed out at {settings.ollama_url}",
                },
                headers=CORS_HEADERS,
            )

    @router.api_route("/api/{path:path}", methods=["GET", "POST", "OPTIONS"])
    async def proxy(path: str, request: Request) -> Response:
        if request.method == "OPTIONS":
            return Response(headers=CORS_HEADERS)

        if settings.auth_enabled:
            auth_header = request.headers.get("authorization", "")
            expected = f"Bearer {settings.auth_token}"
            if auth_header != expected:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or missing authentication token"},
                    headers=CORS_HEADERS,
                )

        target_url = f"{settings.ollama_url}/api/{path}"
        body = await request.body()
        headers = {
            k: v for k, v in request.headers.items() if k.lower() not in ("host", "authorization")
        }

        is_stream = False
        if body:
            try:
                payload = json.loads(body)
                is_stream = payload.get("stream", False)
            except (json.JSONDecodeError, ValueError):
                pass

        try:
            async with httpx.AsyncClient(timeout=settings.timeout) as client:
                if is_stream and request.method == "POST":
                    req = client.build_request(
                        method="POST",
                        url=target_url,
                        content=body,
                        headers=headers,
                    )
                    response = await client.send(req, stream=True)

                    async def stream_response() -> AsyncGenerator[bytes, None]:
                        try:
                            async for chunk in response.aiter_bytes():
                                yield chunk
                        finally:
                            await response.aclose()

                    return StreamingResponse(
                        stream_response(),
                        status_code=response.status_code,
                        headers={
                            **CORS_HEADERS,
                            "Content-Type": response.headers.get(
                                "content-type", "text/event-stream"
                            ),
                        },
                    )
                else:
                    resp = await client.request(
                        method=request.method,
                        url=target_url,
                        content=body,
                        headers=headers,
                    )
                    return JSONResponse(
                        content=resp.json(),
                        status_code=resp.status_code,
                        headers=CORS_HEADERS,
                    )
        except httpx.ConnectError:
            return JSONResponse(
                status_code=502,
                content={
                    "detail": f"Cannot connect to Ollama at {settings.ollama_url}",
                },
                headers=CORS_HEADERS,
            )
        except httpx.TimeoutException:
            return JSONResponse(
                status_code=504,
                content={
                    "detail": f"Request to Ollama timed out at {settings.ollama_url}",
                },
                headers=CORS_HEADERS,
            )

    app.include_router(router)
    return app
