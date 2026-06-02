"""Seed inicial: cria usuário admin, fazenda demo, talhão e sensor.

Uso:
    python scripts/seed.py

Pré-requisitos:
    - Stack rodando (`make up`)
    - Certificados TLS gerados (`make certs`) ou rodar contra `http://localhost:8001..8003`
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from urllib.parse import urljoin

import httpx

BASE_URL = os.environ.get("TERRAMIND_BASE_URL", "https://localhost:8443")
ADMIN_EMAIL = "admin@terramind.local"
ADMIN_PASSWORD = "Terramind#Admin2026"


def url(path: str) -> str:
    return urljoin(BASE_URL.rstrip("/") + "/", path.lstrip("/"))


def main() -> int:
    with httpx.Client(verify=False, timeout=10.0) as client:
        # Tenta criar admin (ignora 409)
        r = client.post(
            url("/auth/register"),
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "full_name": "Admin Terramind",
                "role": "admin",
            },
        )
        if r.status_code not in (201, 409):
            print(f"register failed: {r.status_code} {r.text}", file=sys.stderr)
            return 1

        # Login
        r = client.post(
            url("/auth/login"),
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        if r.status_code != 200:
            print(f"login failed: {r.status_code} {r.text}", file=sys.stderr)
            return 1
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Cria fazenda demo
        r = client.post(
            url("/farm/farms"),
            json={
                "name": "Fazenda Vale Verde",
                "area_ha": 150.5,
                "latitude": -22.123456,
                "longitude": -47.654321,
                "address": "Estrada Rural, km 12 — Piracicaba/SP",
            },
            headers=headers,
        )
        if r.status_code != 201:
            print(f"farm create failed: {r.status_code} {r.text}", file=sys.stderr)
            return 1
        farm_id = r.json()["id"]
        print(f"farm: {farm_id}")

        # Lista culturas e pega 'milho'
        r = client.get(url("/farm/crops"), headers=headers)
        crops = {c["name"]: c["id"] for c in r.json()}
        crop_id = crops.get("milho")

        # Cria talhão
        r = client.post(
            url("/farm/plots"),
            json={
                "farm_id": farm_id,
                "crop_id": crop_id,
                "name": "Talhão A — milho safra 26/27",
                "area_ha": 35.0,
                "planted_at": "2026-04-15",
                "expected_harvest_at": "2026-10-20",
            },
            headers=headers,
        )
        if r.status_code != 201:
            print(f"plot create failed: {r.status_code} {r.text}", file=sys.stderr)
            return 1
        plot_id = r.json()["id"]
        print(f"plot: {plot_id}")

        # Cria sensores
        for stype, serial in (("soil_moisture", "SM-001"), ("temperature", "T-001")):
            r = client.post(
                url("/sensor/sensors"),
                json={
                    "plot_id": plot_id,
                    "type": stype,
                    "serial_number": serial,
                    "status": "active",
                    "description": f"Sensor {stype} demo",
                },
                headers=headers,
            )
            if r.status_code != 201:
                print(f"sensor create failed: {r.status_code} {r.text}", file=sys.stderr)
                return 1
            print(f"sensor {stype}: {r.json()['id']}")

        print("\nseed concluído. credenciais:")
        print(f"  email:    {ADMIN_EMAIL}")
        print(f"  password: {ADMIN_PASSWORD}")
        print(f"\ndatetime: {datetime.now(UTC).isoformat()}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
