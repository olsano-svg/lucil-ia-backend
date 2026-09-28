# Script de Autoconfiguracion y Ejecucion del Backend de Lucil AI
# Para uso en Windows

$ErrorActionPreference = "Stop"

Write-Host "Iniciando configuracion de Lucil AI (Modo Personal)..." -ForegroundColor Cyan

# 1. Comprobar Python
Write-Host "Verificando instalacion de Python..."
try {
    $pythonCmd = "python"
    $pythonVersion = & $pythonCmd --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python fallo"
    }
    Write-Host "Python detectado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python no esta instalado o no se encuentra en el PATH." -ForegroundColor Yellow
    Write-Host "Iniciando proceso de instalacion..."
    
    try {
        $wingetCheck = Get-Command winget -ErrorAction Stop
        Write-Host "Usando winget para instalar Python..."
        winget install --id Python.Python.3.11 --exact --quiet --accept-package-agreements --accept-source-agreements
        Write-Host "ATENCION: Python se ha instalado. Cierra y abre la ventana." -ForegroundColor Red
        Pause
        exit
    } catch {
        Write-Host "winget no esta disponible en tu sistema." -ForegroundColor Red
        Write-Host ""
        Write-Host "============== ACCION MANUAL REQUERIDA ==============" -ForegroundColor Cyan
        Write-Host "Instala Python manualmente:"
        Write-Host "1. Ve a https://www.python.org/downloads/"
        Write-Host "2. Descarga Python 3.10 o superior."
        Write-Host "3. MUY IMPORTANTE: En el instalador, marca 'Add Python to PATH'."
        Write-Host "4. Cierra y vuelve a abrir PowerShell."
        Write-Host "=====================================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Abriendo la pagina por ti..."
        Start-Process "https://www.python.org/downloads/"
        Pause
        exit
    }
}

# 2. Entorno Virtual y Dependencias
Write-Host "Configurando entorno virtual..."
python -m venv venv
.\venv\Scripts\Activate.ps1

Write-Host "Instalando dependencias del backend..."
pip install -r requirements.txt
pip install aiosqlite

# 3. Base de Datos
Write-Host "Inicializando base de datos local (SQLite)..."
alembic upgrade head

# 4. Iniciar Servidor
Write-Host "Iniciando el cerebro de Lucil AI en el puerto 8081..." -ForegroundColor Green
uvicorn app.main:app --host 0.0.0.0 --port 8081
