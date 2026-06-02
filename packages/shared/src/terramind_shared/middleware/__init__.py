"""Middlewares: request_id, security headers e handlers globais de erro."""

from terramind_shared.middleware.error_handler import register_exception_handlers
from terramind_shared.middleware.request_id import RequestIdMiddleware
from terramind_shared.middleware.security_headers import SecurityHeadersMiddleware

__all__ = [
    "RequestIdMiddleware",
    "SecurityHeadersMiddleware",
    "register_exception_handlers",
]
