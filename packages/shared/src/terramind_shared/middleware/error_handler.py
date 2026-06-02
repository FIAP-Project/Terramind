"""Handlers globais de exceção com resposta JSON padronizada.

Formato unificado:

    {
      "error": {
        "code": 422,
        "message": "Validation failed",
        "request_id": "...",
        "details": [...]   // só presente em 422
      }
    }

Nunca expõe stack trace ou detalhes internos do ORM — o detalhe completo
é logado server-side com `structlog` para correlação por `request_id`.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _envelope(
    *,
    code: int,
    message: str,
    request_id: str,
    details: Any = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message, "request_id": request_id}
    if details is not None:
        error["details"] = details
    return {"error": error}


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = _request_id(request)
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(
            code=exc.status_code,
            message=str(exc.detail) if exc.detail else "error",
            request_id=request_id,
        ),
        headers=getattr(exc, "headers", None) or {},
    )


async def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = _request_id(request)
    details = [
        {
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_envelope(
            code=422,
            message="validation failed",
            request_id=request_id,
            details=details,
        ),
    )


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = _request_id(request)
    logger.exception(
        "unhandled exception", extra={"request_id": request_id, "path": str(request.url.path)}
    )
    return JSONResponse(
        status_code=500,
        content=_envelope(
            code=500,
            message="internal server error",
            request_id=request_id,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Anexa os handlers globais ao FastAPI app."""
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
