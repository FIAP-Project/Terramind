"""Controllers do satellite-service."""

from satellite_service.controllers.reading_controller import router as reading_router
from satellite_service.controllers.satellite_controller import router as satellite_router

__all__ = ["reading_router", "satellite_router"]
