"""Assinatura HMAC-SHA256 de payloads de evento.

Cada evento publicado leva um header `x-signature` com o HMAC do corpo JSON.
Consumidores validam antes de processar — garante integridade (sem TLS no
barramento interno) e impede injeção de eventos forjados.
"""

from __future__ import annotations

import hashlib
import hmac


def sign_payload(secret: str, body: bytes) -> str:
    """Assina `body` com HMAC-SHA256 usando `secret`. Retorna hex."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    """Comparação em tempo constante."""
    expected = sign_payload(secret, body)
    return hmac.compare_digest(expected, signature)
