"""Cross-platform task runner para Terramind.

Uso:
    python scripts/tasks.py <comando>

Funciona identicamente em macOS, Linux e Windows.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CERTS_DIR = ROOT / "infra" / "nginx" / "certs"


def run(cmd: list[str], **kwargs: object) -> int:
    """Executa um comando, herdando stdout/stderr."""
    print(f"$ {' '.join(cmd)}", flush=True)
    return subprocess.call(cmd, cwd=str(ROOT), **kwargs)  # noqa: S603


def cmd_help() -> int:
    print(
        "Terramind — comandos disponíveis:\n"
        "  python scripts/tasks.py sync     — uv sync\n"
        "  python scripts/tasks.py up       — docker compose up --build -d\n"
        "  python scripts/tasks.py down     — docker compose down\n"
        "  python scripts/tasks.py restart  — restart containers\n"
        "  python scripts/tasks.py logs     — tail logs\n"
        "  python scripts/tasks.py ps       — listar containers\n"
        "  python scripts/tasks.py test     — uv run pytest\n"
        "  python scripts/tasks.py fmt      — ruff format\n"
        "  python scripts/tasks.py lint     — ruff check\n"
        "  python scripts/tasks.py certs    — gerar TLS de dev\n"
        "  python scripts/tasks.py clean    — remover containers e caches"
    )
    return 0


def cmd_sync() -> int:
    return run(["uv", "sync"])


def cmd_up() -> int:
    rc = run(["docker", "compose", "up", "--build", "-d"])
    if rc == 0:
        print(
            "\nAguarde alguns segundos e acesse:\n"
            "  Swagger auth:   https://localhost:8443/auth/docs\n"
            "  Swagger farm:   https://localhost:8443/farm/docs\n"
            "  Swagger sensor: https://localhost:8443/sensor/docs\n"
            "  Swagger alert:  https://localhost:8443/alert/docs"
        )
    return rc


def cmd_down() -> int:
    return run(["docker", "compose", "down"])


def cmd_restart() -> int:
    return run(["docker", "compose", "restart"])


def cmd_logs() -> int:
    return run(["docker", "compose", "logs", "-f", "--tail=100"])


def cmd_ps() -> int:
    return run(["docker", "compose", "ps"])


def cmd_test() -> int:
    return run(["uv", "run", "pytest", "-q"])


def cmd_fmt() -> int:
    return run(["uv", "run", "ruff", "format", "."])


def cmd_lint() -> int:
    return run(["uv", "run", "ruff", "check", "."])


def cmd_certs() -> int:
    CERTS_DIR.mkdir(parents=True, exist_ok=True)
    mkcert = shutil.which("mkcert")
    if mkcert:
        print("Usando mkcert...")
        subprocess.run([mkcert, "-install"], check=False)  # noqa: S603
        subprocess.run(  # noqa: S603
            [mkcert, "localhost", "127.0.0.1", "::1"],
            cwd=str(CERTS_DIR),
            check=False,
        )
        cert = CERTS_DIR / "localhost+2.pem"
        key = CERTS_DIR / "localhost+2-key.pem"
        if cert.exists():
            cert.rename(CERTS_DIR / "cert.pem")
        if key.exists():
            key.rename(CERTS_DIR / "key.pem")
    else:
        print("mkcert não encontrado — usando OpenSSL self-signed...")
        openssl = shutil.which("openssl")
        if not openssl:
            print(
                "ERRO: nem mkcert nem openssl encontrados. "
                "Instale um dos dois e tente novamente."
            )
            return 1
        subprocess.run(  # noqa: S603
            [
                openssl, "req", "-x509", "-nodes", "-newkey", "rsa:2048",
                "-days", "365",
                "-keyout", str(CERTS_DIR / "key.pem"),
                "-out", str(CERTS_DIR / "cert.pem"),
                "-subj", "/CN=localhost",
                "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
            ],
            check=False,
        )
    print(f"Certificados gerados em {CERTS_DIR}")
    return 0


def cmd_clean() -> int:
    run(["docker", "compose", "down", "-v"])
    patterns = ["__pycache__", ".pytest_cache", ".ruff_cache"]
    for pattern in patterns:
        for path in ROOT.rglob(pattern):
            print(f"removing {path}")
            shutil.rmtree(path, ignore_errors=True)
    for egg in ROOT.rglob("*.egg-info"):
        shutil.rmtree(egg, ignore_errors=True)
    return 0


COMMANDS = {
    "help": cmd_help,
    "sync": cmd_sync,
    "up": cmd_up,
    "down": cmd_down,
    "restart": cmd_restart,
    "logs": cmd_logs,
    "ps": cmd_ps,
    "test": cmd_test,
    "fmt": cmd_fmt,
    "lint": cmd_lint,
    "certs": cmd_certs,
    "clean": cmd_clean,
}


def main() -> int:
    if len(sys.argv) < 2:
        return cmd_help()
    command = sys.argv[1].lower()
    handler = COMMANDS.get(command)
    if handler is None:
        print(f"Comando desconhecido: {command}\n")
        cmd_help()
        return 1
    return handler()


if __name__ == "__main__":
    sys.exit(main())
