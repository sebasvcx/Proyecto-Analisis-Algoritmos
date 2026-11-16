# Levanta backend (FastAPI, puerto 8000) y frontend (Vite, puerto 5173) juntos en Windows.
# Equivalente a dev.sh. Ctrl+C detiene ambos.
# Uso: powershell -ExecutionPolicy Bypass -File .\dev.ps1
$ErrorActionPreference = "Stop"

$Raiz = $PSScriptRoot
$Venv = Join-Path $Raiz "backend\.venv"
$Python = Join-Path $Venv "Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "-> Creando entorno de Python 3.12 e instalando dependencias..."
    py -V:3.12 -m venv $Venv
    if (-not $?) { throw "No se pudo crear el entorno. Instale Python 3.12 con: py install 3.12" }
    & $Python -m pip install -q --disable-pip-version-check -r (Join-Path $Raiz "backend\requirements.txt")
}

if (-not (Test-Path (Join-Path $Raiz "frontend\node_modules"))) {
    Write-Host "-> Instalando dependencias del frontend..."
    Push-Location (Join-Path $Raiz "frontend")
    npm install
    Pop-Location
}

$Backend = Start-Process -FilePath $Python `
    -ArgumentList "-m", "uvicorn", "api.main:app", "--reload", "--port", "8000" `
    -WorkingDirectory (Join-Path $Raiz "backend") -NoNewWindow -PassThru

try {
    Push-Location (Join-Path $Raiz "frontend")
    npm run dev
}
finally {
    Pop-Location
    if (-not $Backend.HasExited) {
        # /T cierra también el proceso hijo que crea --reload
        taskkill /PID $Backend.Id /T /F | Out-Null
    }
}
