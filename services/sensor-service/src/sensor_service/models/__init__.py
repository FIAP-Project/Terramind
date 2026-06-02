"""Modelos SQLAlchemy do sensor-service."""

from sensor_service.models.reading import Reading
from sensor_service.models.sensor import Sensor

__all__ = ["Reading", "Sensor"]
