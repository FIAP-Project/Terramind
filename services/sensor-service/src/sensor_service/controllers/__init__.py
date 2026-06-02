"""Controllers do sensor-service."""

from sensor_service.controllers.reading_controller import router as reading_router
from sensor_service.controllers.sensor_controller import router as sensor_router

__all__ = ["reading_router", "sensor_router"]
