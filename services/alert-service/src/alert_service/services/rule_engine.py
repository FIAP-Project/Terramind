"""Motor de regras para gerar alertas a partir de leituras.

Versão MVP: regras hardcoded por tipo de sensor com limiares de fallback.
Em produção evoluiria para regras dinâmicas associadas a Crop específica.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleResult:
    triggered: bool
    severity: str
    rule_id: str
    message: str


@dataclass(frozen=True)
class Thresholds:
    humidity_min: float
    humidity_max: float
    temp_min: float
    temp_max: float


class RuleEngine:
    def __init__(self, thresholds: Thresholds) -> None:
        self._t = thresholds

    def evaluate(
        self,
        *,
        sensor_type: str,
        value: float,
        unit: str,
    ) -> RuleResult:
        if sensor_type == "soil_moisture":
            return self._evaluate_humidity(value)
        if sensor_type == "temperature":
            return self._evaluate_temperature(value)
        if sensor_type == "rainfall":
            return self._evaluate_rainfall(value, unit)
        return RuleResult(triggered=False, severity="info", rule_id="noop", message="no rule")

    def _evaluate_humidity(self, value: float) -> RuleResult:
        if value < self._t.humidity_min:
            severity = "critical" if value < self._t.humidity_min - 10 else "warning"
            return RuleResult(
                triggered=True,
                severity=severity,
                rule_id="humidity.below_min",
                message=f"soil moisture below minimum: {value:.2f}%",
            )
        if value > self._t.humidity_max:
            return RuleResult(
                triggered=True,
                severity="warning",
                rule_id="humidity.above_max",
                message=f"soil moisture above maximum: {value:.2f}%",
            )
        return RuleResult(triggered=False, severity="info", rule_id="humidity.ok", message="ok")

    def _evaluate_temperature(self, value: float) -> RuleResult:
        if value < self._t.temp_min:
            return RuleResult(
                triggered=True,
                severity="warning",
                rule_id="temperature.below_min",
                message=f"temperature below minimum: {value:.2f}°C",
            )
        if value > self._t.temp_max:
            severity = "critical" if value > self._t.temp_max + 5 else "warning"
            return RuleResult(
                triggered=True,
                severity=severity,
                rule_id="temperature.above_max",
                message=f"temperature above maximum: {value:.2f}°C",
            )
        return RuleResult(
            triggered=False, severity="info", rule_id="temperature.ok", message="ok"
        )

    def _evaluate_rainfall(self, value: float, unit: str) -> RuleResult:
        # Acima de 80mm em 24h pode indicar enchente.
        threshold = 80.0
        if unit.lower() in {"mm", "millimeter"} and value > threshold:
            return RuleResult(
                triggered=True,
                severity="critical",
                rule_id="rainfall.flood_risk",
                message=f"heavy rainfall detected: {value:.2f}mm",
            )
        return RuleResult(triggered=False, severity="info", rule_id="rainfall.ok", message="ok")
