"""Seed inicial: cria usuário admin, fazenda demo, talhão e satélite.

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
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "Terramind#Admin2026"


def url(path: str) -> str:
    return urljoin(BASE_URL.rstrip("/") + "/", path.lstrip("/"))


def find_farm_id(client: httpx.Client, headers: dict[str, str], name: str) -> str | None:
    r = client.get(url("/farm/farms"), headers=headers)
    if r.status_code != 200:
        print(f"farm list failed: {r.status_code} {r.text}", file=sys.stderr)
        return None
    for farm in r.json():
        if farm.get("name") == name:
            return farm["id"]
    return None


def find_plot_id(
    client: httpx.Client,
    headers: dict[str, str],
    *,
    farm_id: str,
    name: str,
) -> str | None:
    r = client.get(url(f"/farm/plots?farm_id={farm_id}"), headers=headers)
    if r.status_code != 200:
        print(f"plot list failed: {r.status_code} {r.text}", file=sys.stderr)
        return None
    for plot in r.json():
        if plot.get("name") == name:
            return plot["id"]
    return None


def find_satellite_id(
    client: httpx.Client,
    headers: dict[str, str],
    *,
    serial_number: str,
) -> str | None:
    r = client.get(url("/satellite/satellites"), headers=headers)
    if r.status_code != 200:
        print(f"satellite list failed: {r.status_code} {r.text}", file=sys.stderr)
        return None
    for satellite in r.json():
        if satellite.get("serial_number") == serial_number:
            return satellite["id"]
    return None


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

        farm_name = "Fazenda Vale Verde"
        farm_id = find_farm_id(client, headers, farm_name)
        if farm_id is None:
            r = client.post(
                url("/farm/farms"),
                json={
                    "name": farm_name,
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
            print(f"farm created: {farm_id}")
        else:
            print(f"farm reused: {farm_id}")

        # Lista culturas e pega 'milho'
        r = client.get(url("/farm/crops"), headers=headers)
        crops = {c["name"]: c["id"] for c in r.json()}
        crop_id = crops.get("milho")

        plot_name = "Talhão A — milho safra 26/27"
        plot_id = find_plot_id(client, headers, farm_id=farm_id, name=plot_name)
        if plot_id is None:
            r = client.post(
                url("/farm/plots"),
                json={
                    "farm_id": farm_id,
                    "crop_id": crop_id,
                    "name": plot_name,
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
            print(f"plot created: {plot_id}")
        else:
            print(f"plot reused: {plot_id}")

        # Cria satélites
        for stype, serial in (("soil_moisture", "SM-001"), ("temperature", "T-001")):
            satellite_id = find_satellite_id(
                client,
                headers,
                serial_number=serial,
            )
            if satellite_id is not None:
                print(f"satellite {stype} reused: {satellite_id}")
                continue
            r = client.post(
                url("/satellite/satellites"),
                json={
                    "plot_id": plot_id,
                    "type": stype,
                    "serial_number": serial,
                    "status": "active",
                    "description": f"Satellite {stype} demo",
                },
                headers=headers,
            )
            if r.status_code != 201:
                print(f"satellite create failed: {r.status_code} {r.text}", file=sys.stderr)
                return 1
            print(f"satellite {stype} created: {r.json()['id']}")

        print("\nseed concluído. credenciais:")
        print(f"  email:    {ADMIN_EMAIL}")
        print(f"  password: {ADMIN_PASSWORD}")
        print(f"\ndatetime: {datetime.now(UTC).isoformat()}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
