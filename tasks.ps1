# Terramind — task runner para Windows PowerShell
# Uso: .\tasks.ps1 <comando>

param(
    [Parameter(Position = 0)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host "Terramind - comandos disponiveis:"
    Write-Host "  .\tasks.ps1 sync     - uv sync (instalar workspace)"
    Write-Host "  .\tasks.ps1 up       - docker compose up --build -d"
    Write-Host "  .\tasks.ps1 down     - docker compose down"
    Write-Host "  .\tasks.ps1 restart  - restart all containers"
    Write-Host "  .\tasks.ps1 logs     - tail logs"
    Write-Host "  .\tasks.ps1 ps       - listar containers"
    Write-Host "  .\tasks.ps1 test     - uv run pytest"
    Write-Host "  .\tasks.ps1 fmt      - ruff format"
    Write-Host "  .\tasks.ps1 lint     - ruff check"
    Write-Host "  .\tasks.ps1 certs    - gerar certificados TLS de dev"
    Write-Host "  .\tasks.ps1 clean    - remover containers, volumes, caches"
}

function Invoke-Sync { uv sync }

function Invoke-Up {
    docker compose up --build -d
    Write-Host ""
    Write-Host "Aguarde alguns segundos e acesse:"
    Write-Host "  Swagger auth:   https://localhost:8443/auth/docs"
    Write-Host "  Swagger farm:   https://localhost:8443/farm/docs"
    Write-Host "  Swagger sensor: https://localhost:8443/sensor/docs"
    Write-Host "  Swagger alert:  https://localhost:8443/alert/docs"
}

function Invoke-Down { docker compose down }
function Invoke-Restart { docker compose restart }
function Invoke-Logs { docker compose logs -f --tail=100 }
function Invoke-Ps { docker compose ps }
function Invoke-Test { uv run pytest -q }
function Invoke-Fmt { uv run ruff format . }
function Invoke-Lint { uv run ruff check . }

function Invoke-Certs {
    $certsDir = "infra\nginx\certs"
    New-Item -ItemType Directory -Force -Path $certsDir | Out-Null
    if (Get-Command mkcert -ErrorAction SilentlyContinue) {
        Push-Location $certsDir
        mkcert -install
        mkcert localhost 127.0.0.1 ::1
        if (Test-Path "localhost+2.pem") { Move-Item -Force "localhost+2.pem" "cert.pem" }
        if (Test-Path "localhost+2-key.pem") { Move-Item -Force "localhost+2-key.pem" "key.pem" }
        Pop-Location
    } else {
        Write-Host "mkcert nao encontrado. Use OpenSSL ou instale mkcert via chocolatey: choco install mkcert"
        Write-Host "Tentando OpenSSL..."
        & openssl req -x509 -nodes -newkey rsa:2048 -days 365 `
            -keyout "$certsDir\key.pem" `
            -out "$certsDir\cert.pem" `
            -subj "/CN=localhost" `
            -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
    }
    Write-Host "Certificados gerados em $certsDir"
}

function Invoke-Clean {
    docker compose down -v
    Get-ChildItem -Path . -Recurse -Force -Include "__pycache__", ".pytest_cache", ".ruff_cache", "*.egg-info" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force
}

switch ($Command.ToLower()) {
    "help"    { Show-Help }
    "sync"    { Invoke-Sync }
    "up"      { Invoke-Up }
    "down"    { Invoke-Down }
    "restart" { Invoke-Restart }
    "logs"    { Invoke-Logs }
    "ps"      { Invoke-Ps }
    "test"    { Invoke-Test }
    "fmt"     { Invoke-Fmt }
    "lint"    { Invoke-Lint }
    "certs"   { Invoke-Certs }
    "clean"   { Invoke-Clean }
    default   {
        Write-Host "Comando desconhecido: $Command"
        Show-Help
        exit 1
    }
}
