"""Endpoints HTTP do auth-service."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from auth_service.dependencies import (
    get_auth_service,
    get_user_repository,
)
from auth_service.repositories import UserRepository
from auth_service.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)
from auth_service.services import (
    AuthService,
    EmailAlreadyTakenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from terramind_shared.security import Principal, get_current_principal

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um novo usuário",
)
async def register(
    payload: RegisterRequest,
    auth: AuthService = Depends(get_auth_service),
) -> UserOut:
    try:
        return await auth.register(payload)
    except EmailAlreadyTakenError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already registered",
        ) from exc


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Autentica e retorna o par de tokens (access + refresh)",
)
async def login(
    payload: LoginRequest,
    auth: AuthService = Depends(get_auth_service),
) -> TokenPair:
    try:
        return await auth.login(str(payload.email), payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Rotaciona o par de tokens a partir de um refresh válido",
)
async def refresh(
    payload: RefreshRequest,
    auth: AuthService = Depends(get_auth_service),
) -> TokenPair:
    try:
        return await auth.refresh(payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.get(
    "/me",
    response_model=UserOut,
    summary="Retorna o usuário autenticado",
)
async def me(
    principal: Principal = Depends(get_current_principal),
    users: UserRepository = Depends(get_user_repository),
) -> UserOut:
    user = await users.get_by_id(UUID(principal.user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return UserOut.model_validate(user)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove o usuário autenticado (LGPD — direito de exclusão)",
)
async def delete_me(
    principal: Principal = Depends(get_current_principal),
    users: UserRepository = Depends(get_user_repository),
) -> None:
    user = await users.get_by_id(UUID(principal.user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    await users.delete(user)
