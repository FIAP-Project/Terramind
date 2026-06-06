"""Simula leituras de satélites enviando POSTs para o satellite-service.

Uso:
    python scripts/simulate_readings.py [--interval 5] [--cycles 20]

Login com admin, lista satélites ativos e envia leituras com pequenas
oscilações em torno do limite — alguns valores fora da faixa para
demonstrar a geração de alertas pelo alert-service.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import UTC, datetime
from urllib.parse import urljoin

import httpx

BASE_URL = os.environ.get("TERRAMIND_BASE_URL", "https://localhost:8443")
ADMIN_EMAIL = os.environ.get("TERRAMIND_ADMIN_EMAIL", "admin@gmail.com")
ADMIN_PASSWORD = os.environ.get("TERRAMIND_ADMIN_PASSWORD", "Terramind#Admin2026")


def url(path: str) -> str:
    return urljoin(BASE_URL.rstrip("/") + "/", path.lstrip("/"))


def value_for(satellite_type: str) -> tuple[float, str]:
    if satellite_type == "soil_moisture":
        return round(random.uniform(20.0, 90.0), 2), "pct"
    if satellite_type == "temperature":
        return round(random.uniform(0.0, 45.0), 2), "celsius"
    if satellite_type == "rainfall":
        return round(random.uniform(0.0, 120.0), 2), "mm"
    return round(random.uniform(0.0, 100.0), 2), "unit"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=5.0, help="segundos entre rodadas")
    parser.add_argument("--cycles", type=int, default=20, help="número de rodadas")
    args = parser.parse_args()

    with httpx.Client(verify=False, timeout=10.0) as client:
        r = client.post(
            url("/auth/login"),
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        if r.status_code != 200:
            print(f"login failed: {r.status_code} {r.text}", file=sys.stderr)
            return 1
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r = client.get(url("/satellite/satellites"), headers=headers)
        satellites = [s for s in r.json() if s.get("status") == "active"]
        if not satellites:
            print("nenhum satélite ativo. rode `python scripts/seed.py` antes.", file=sys.stderr)
            return 1

        print(f"simulando {args.cycles} rodadas em {len(satellites)} satélites")

        for cycle in range(1, args.cycles + 1):
            for satellite in satellites:
                value, unit = value_for(satellite["type"])
                payload = {
                    "value": value,
                    "unit": unit,
                    "captured_at": datetime.now(UTC).isoformat(),
                }
                r = client.post(
                    url(f"/satellite/satellites/{satellite['id']}/readings"),
                    json=payload,
                    headers=headers,
                )
                status = "ok" if r.status_code == 201 else f"err {r.status_code}"
                print(
                    f"cycle={cycle:02d} satellite={satellite['serial_number']} "
                    f"type={satellite['type']} value={value} {unit} → {status}"
                )
            if cycle < args.cycles:
                time.sleep(args.interval)

        print("\nleituras enviadas. consulte alertas em /alert/alerts")
        return 0


if __name__ == "__main__":
    sys.exit(main())
