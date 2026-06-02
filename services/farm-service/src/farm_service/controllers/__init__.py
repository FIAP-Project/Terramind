"""Controllers do farm-service."""

from farm_service.controllers.crop_controller import router as crop_router
from farm_service.controllers.farm_controller import router as farm_router
from farm_service.controllers.plot_controller import router as plot_router

__all__ = ["crop_router", "farm_router", "plot_router"]
