"""Controle de acesso baseado em papéis (RBAC).

Hierarquia: PRODUCER < AGRONOMIST < ADMIN.
Dependency factory `require_role(Role.X)` exige que o `Principal` autenticado
tenha papel >= X.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum

from fastapi import Depends, HTTPException, status


class Role(StrEnum):
    PRODUCER = "producer"
    AGRONOMIST = "agronomist"
    ADMIN = "admin"


_HIERARCHY: dict[Role, int] = {
    Role.PRODUCER: 0,
    Role.AGRONOMIST: 1,
    Role.ADMIN: 2,
}


def role_at_least(actual: Role | str, required: Role) -> bool:
    """True se `actual` é >= `required` na hierarquia."""
    try:
        actual_role = Role(actual) if not isinstance(actual, Role) else actual
    except ValueError:
        return False
    return _HIERARCHY[actual_role] >= _HIERARCHY[required]


def require_role(required: Role) -> Callable:
    """Dependency factory do FastAPI.

    Importação tardia para evitar ciclo: `dependencies` importa daqui.
    """
    from terramind_shared.security.dependencies import Principal, get_current_principal

    def _check(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not role_at_least(principal.role, required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role '{required.value}' required",
            )
        return principal

    return _check
