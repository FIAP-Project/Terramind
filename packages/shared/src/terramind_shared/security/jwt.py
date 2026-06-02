"""Emissão e validação de JWT (HS256).

Tokens carregam: sub (user_id), email, role, iat, exp, jti, token_type.
`access` tokens têm TTL curto (15 min); `refresh` tokens têm TTL longo (7 dias)
e são rastreados em banco via `jti` para suportar revogação.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict


class InvalidTokenError(Exception):
    """Token expirado, malformado, com assinatura inválida ou tipo errado."""


class TokenPayload(BaseModel):
    """Claims tipadas extraídas de um token decodificado."""

    model_config = ConfigDict(frozen=True)

    sub: str
    email: str
    role: str
    iat: int
    exp: int
    jti: str
    token_type: str


class JWTService:
    """Emissor/validador de JWT compartilhado pelos serviços."""

    def __init__(
        self,
        secret: str,
        *,
        algorithm: str = "HS256",
        access_ttl_minutes: int = 15,
        refresh_ttl_days: int = 7,
    ) -> None:
        if len(secret) < 32:
            raise ValueError("JWT secret must be at least 32 characters")
        self._secret = secret
        self._algorithm = algorithm
        self._access_ttl = timedelta(minutes=access_ttl_minutes)
        self._refresh_ttl = timedelta(days=refresh_ttl_days)

    @property
    def access_ttl_seconds(self) -> int:
        return int(self._access_ttl.total_seconds())

    @property
    def refresh_ttl_seconds(self) -> int:
        return int(self._refresh_ttl.total_seconds())

    def issue_access(self, *, user_id: str, email: str, role: str) -> tuple[str, str]:
        """Emite um access token. Retorna (token, jti)."""
        return self._issue(
            user_id=user_id, email=email, role=role, ttl=self._access_ttl, token_type="access"
        )

    def issue_refresh(self, *, user_id: str, email: str, role: str) -> tuple[str, str]:
        """Emite um refresh token. Retorna (token, jti)."""
        return self._issue(
            user_id=user_id, email=email, role=role, ttl=self._refresh_ttl, token_type="refresh"
        )

    def _issue(
        self, *, user_id: str, email: str, role: str, ttl: timedelta, token_type: str
    ) -> tuple[str, str]:
        now = datetime.now(UTC)
        jti = str(uuid4())
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int((now + ttl).timestamp()),
            "jti": jti,
            "token_type": token_type,
        }
        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        return token, jti

    def decode(self, token: str, *, expected_type: str = "access") -> TokenPayload:
        """Decodifica e valida assinatura, expiração e tipo do token."""
        try:
            raw = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except JWTError as exc:
            raise InvalidTokenError(str(exc)) from exc
        try:
            payload = TokenPayload(**raw)
        except (TypeError, ValueError) as exc:
            raise InvalidTokenError(f"invalid token claims: {exc}") from exc
        if payload.token_type != expected_type:
            raise InvalidTokenError(
                f"expected '{expected_type}' token, got '{payload.token_type}'"
            )
        return payload
