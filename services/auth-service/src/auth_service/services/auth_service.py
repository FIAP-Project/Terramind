"""Lógica de negócio do auth-service.

Orquestra repositórios, JWT, hashing e eventos. Sem dependências do FastAPI.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError

from auth_service.repositories import RefreshTokenRepository, UserRepository
from auth_service.schemas.auth import RegisterRequest, TokenPair, UserOut
from terramind_shared.events import EventBus, EventType
from terramind_shared.events.schemas import (
    AuthFailedEvent,
    UserLoggedInEvent,
    UserRegisteredEvent,
)
from terramind_shared.security import (
    InvalidTokenError,
    JWTService,
    Role,
    hash_password,
    verify_password,
)


class EmailAlreadyTakenError(Exception):
    """Já existe um usuário com este email."""


class InvalidCredentialsError(Exception):
    """Email ou senha inválidos."""


class InvalidRefreshTokenError(Exception):
    """Refresh token expirado, revogado ou desconhecido."""


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        jwt: JWTService,
        event_bus: EventBus,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._jwt = jwt
        self._events = event_bus

    async def register(self, payload: RegisterRequest) -> UserOut:
        role = (payload.role or Role.PRODUCER).value
        try:
            user = await self._users.create(
                email=str(payload.email),
                password_hash=hash_password(payload.password),
                role=role,
                full_name=payload.full_name,
            )
        except IntegrityError as exc:
            raise EmailAlreadyTakenError(str(payload.email)) from exc

        await self._events.publish(
            EventType.USER_REGISTERED.value,
            UserRegisteredEvent(
                user_id=str(user.id),
                email=user.email,
                role=user.role,
                actor_user_id=str(user.id),
            ).model_dump(mode="json"),
        )
        return UserOut.model_validate(user)

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            await self._events.publish(
                EventType.AUTH_FAILED.value,
                AuthFailedEvent(email=email, reason="invalid_credentials").model_dump(
                    mode="json"
                ),
            )
            raise InvalidCredentialsError("invalid email or password")

        return await self._issue_pair(user_id=str(user.id), email=user.email, role=user.role)

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = self._jwt.decode(refresh_token, expected_type="refresh")
        except InvalidTokenError as exc:
            raise InvalidRefreshTokenError(str(exc)) from exc

        stored = await self._refresh_tokens.get_by_jti(payload.jti)
        if stored is None or stored.revoked:
            raise InvalidRefreshTokenError("refresh token not active")
        if stored.expires_at < datetime.now(UTC):
            raise InvalidRefreshTokenError("refresh token expired")

        # Rotation: revoga o atual e emite um novo par.
        await self._refresh_tokens.revoke_by_jti(payload.jti)
        return await self._issue_pair(
            user_id=payload.sub, email=payload.email, role=payload.role
        )

    async def _issue_pair(self, *, user_id: str, email: str, role: str) -> TokenPair:
        access_token, _ = self._jwt.issue_access(user_id=user_id, email=email, role=role)
        refresh_token, refresh_jti = self._jwt.issue_refresh(
            user_id=user_id, email=email, role=role
        )
        expires_at = datetime.now(UTC) + timedelta(seconds=self._jwt.refresh_ttl_seconds)
        from uuid import UUID

        await self._refresh_tokens.create(
            user_id=UUID(user_id), jti=refresh_jti, expires_at=expires_at
        )
        await self._events.publish(
            EventType.USER_LOGGED_IN.value,
            UserLoggedInEvent(user_id=user_id, email=email, actor_user_id=user_id).model_dump(
                mode="json"
            ),
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._jwt.access_ttl_seconds,
        )
