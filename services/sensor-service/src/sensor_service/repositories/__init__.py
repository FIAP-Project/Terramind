"""Repositórios do sensor-service."""

from sensor_service.repositories.reading_repository import ReadingRepository
from sensor_service.repositories.sensor_repository import SensorRepository

__all__ = ["ReadingRepository", "SensorRepository"]
