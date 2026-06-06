"""DTOs Pydantic do satellite-service."""

from satellite_service.schemas.reading import ReadingCreate, ReadingOut
from satellite_service.schemas.satellite import SatelliteCreate, SatelliteOut, SatelliteUpdate

__all__ = [
    "ReadingCreate",
    "ReadingOut",
    "SatelliteCreate",
    "SatelliteOut",
    "SatelliteUpdate",
]
