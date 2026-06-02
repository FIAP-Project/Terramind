"""DTOs Pydantic do sensor-service."""

from sensor_service.schemas.reading import ReadingCreate, ReadingOut
from sensor_service.schemas.sensor import SensorCreate, SensorOut, SensorUpdate

__all__ = [
    "ReadingCreate",
    "ReadingOut",
    "SensorCreate",
    "SensorOut",
    "SensorUpdate",
]
