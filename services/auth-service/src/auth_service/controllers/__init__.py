"""Controllers (routers FastAPI) do auth-service."""

from auth_service.controllers.auth_controller import router as auth_router

__all__ = ["auth_router"]
