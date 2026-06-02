"""Dependencies FastAPI para resolver o usuário autenticado.

Uso típico em um controller:

    from terramind_shared.security import Principal, get_current_principal

    @router.get("/me")
    async def me(principal: Principal = Depends(get_current_principal)):
        ...
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from terramind_shared.security.jwt import InvalidTokenError, JWTService
from terramind_shared.security.rbac import Role

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    """Usuário autenticado, derivado das claims do JWT."""

    user_id: str
    email: str
    role: Role
    jti: str


def get_jwt_service(request: Request) -> JWTService:
    """Recupera o JWTService instanciado no `lifespan` do app."""
    svc = getattr(request.app.state, "jwt_service", None)
    if svc is None:
        raise RuntimeError("JWTService not initialized on app.state")
    return svc


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> Principal:
    """Extrai e valida o Bearer token; retorna o `Principal`."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt_service.decode(credentials.credentials, expected_type="access")
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    try:
        role = Role(payload.role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid role in token",
        ) from exc
    return Principal(
        user_id=payload.sub,
        email=payload.email,
        role=role,
        jti=payload.jti,
    )
