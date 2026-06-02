"""Injeção de dependências do auth-service."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.repositories import RefreshTokenRepository, UserRepository
from auth_service.services import AuthService


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    db = request.app.state.database
    async for session in db.session():
        yield session


def get_auth_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> AuthService:
    return AuthService(
        users=UserRepository(session),
        refresh_tokens=RefreshTokenRepository(session),
        jwt=request.app.state.jwt_service,
        event_bus=request.app.state.event_bus,
    )


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session)
