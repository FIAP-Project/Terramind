"""Hash e verificação de senhas com bcrypt.

Usa SHA256 pré-hash + Base64 antes do bcrypt para evitar o limite de 72 bytes
de input do bcrypt — mantém entropia mesmo com senhas longas.

`passlib[bcrypt]` é preferido a `bcrypt` puro porque o wheel pré-compilado
é mais portável (especialmente no Windows, evita VC++ Build Tools).
"""

from __future__ import annotations

import base64
import hashlib

from passlib.hash import bcrypt

_ROUNDS = 12


def _prepare(plain: str) -> str:
    """Pre-hash com SHA256 + Base64 para ficar dentro do limite do bcrypt."""
    digest = hashlib.sha256(plain.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


def hash_password(plain: str) -> str:
    """Gera um hash bcrypt seguro para `plain`."""
    if not plain:
        raise ValueError("password cannot be empty")
    return bcrypt.using(rounds=_ROUNDS).hash(_prepare(plain))


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica `plain` contra `hashed` em tempo constante."""
    try:
        return bcrypt.verify(_prepare(plain), hashed)
    except (ValueError, TypeError):
        return False
