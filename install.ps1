# install.ps1
# Instala theia-agent en un venv aislado y crea un wrapper global
# Uso: .\install.ps1
# Requiere: Python 3.11+

$ErrorActionPreference = "Stop"

$INSTALL_DIR = "$env:USERPROFILE\.theia-agent"
$VENV_DIR    = "$INSTALL_DIR\venv"
$PKG_DIR     = "$PSScriptRoot"          # la carpeta donde está este script

Write-Host "Instalando theia-agent..." -ForegroundColor Cyan

# 1. Crear venv limpio
if (Test-Path $VENV_DIR) {
    Write-Host "  venv ya existe, actualizando..." -ForegroundColor DarkGray
} else {
    Write-Host "  Creando venv en $VENV_DIR"
    python -m venv $VENV_DIR
}

# 2. Instalar el paquete en el venv (sin tocar el Python global)
& "$VENV_DIR\Scripts\pip" install -e $PKG_DIR --quiet

Write-Host "  Paquete instalado" -ForegroundColor Green

# 3. Crear wrappers .cmd en %USERPROFILE%\.local\bin  (o cualquier dir en PATH)
$BIN_DIR = "$env:USERPROFILE\.local\bin"
New-Item -ItemType Directory -Force -Path $BIN_DIR | Out-Null

# theia.cmd
@"
@echo off
"$VENV_DIR\Scripts\python" -m theia_agent.cli %*
"@ | Set-Content "$BIN_DIR\theia.cmd" -Encoding ASCII

# theia-mcp.cmd
@"
@echo off
"$VENV_DIR\Scripts\python" -m theia_agent.server %*
"@ | Set-Content "$BIN_DIR\theia-mcp.cmd" -Encoding ASCII

Write-Host "  Wrappers creados en $BIN_DIR" -ForegroundColor Green

# 4. Añadir bin dir al PATH de usuario si no está ya
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$BIN_DIR*") {
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$BIN_DIR", "User")
    Write-Host "  $BIN_DIR añadido al PATH de usuario" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Abre una terminal nueva para que el PATH tenga efecto." -ForegroundColor Yellow
} else {
    Write-Host "  PATH ya contiene $BIN_DIR" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Listo. Prueba en cualquier directorio:" -ForegroundColor Green
Write-Host "  theia /list" -ForegroundColor Cyan