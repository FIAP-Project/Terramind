"""Segurança: JWT, hash de senha, RBAC e dependencies de autenticação."""

from terramind_shared.security.dependencies import Principal, get_current_principal
from terramind_shared.security.jwt import InvalidTokenError, JWTService, TokenPayload
from terramind_shared.security.passwords import hash_password, verify_password
from terramind_shared.security.rbac import Role, require_role, role_at_least

__all__ = [
    "InvalidTokenError",
    "JWTService",
    "Principal",
    "Role",
    "TokenPayload",
    "get_current_principal",
    "hash_password",
    "require_role",
    "role_at_least",
    "verify_password",
]
