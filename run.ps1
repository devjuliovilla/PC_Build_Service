$ErrorActionPreference = "Stop"

function Pause-AndExit($message)
{
    Write-Host ""
    Write-Host $message -ForegroundColor Yellow
    Read-Host "Presione ENTER para continuar"
    exit
}

Clear-Host

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "        PYTHON PROJECT LAUNCHER" -ForegroundColor Cyan
Write-Host "============================================="
Write-Host ""

##########################################################
# Verificar Python
##########################################################

try
{
    python --version | Out-Null
}
catch
{
    Pause-AndExit "Python no está instalado o no está en el PATH."
}

##########################################################
# Crear entorno virtual
##########################################################

if (!(Test-Path ".\venv"))
{
    Write-Host "Creando entorno virtual..."
    python -m venv venv

    if ($LASTEXITCODE -ne 0)
    {
        Pause-AndExit "No fue posible crear el entorno virtual."
    }
}

##########################################################
# Activar entorno
##########################################################

Write-Host "Activando entorno virtual..."

. .\venv\Scripts\Activate.ps1

##########################################################
# Instalar dependencias
##########################################################

Write-Host "Verificando dependencias..."

pip install -r requirements.txt

##########################################################
# Instalar Chromium
##########################################################

Write-Host "Verificando Playwright..."

playwright install chromium

##########################################################
# Menú
##########################################################

while ($true)
{
    Clear-Host

    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host "            DDTECH SCRAPER" -ForegroundColor Cyan
    Write-Host "============================================="
    Write-Host ""
    Write-Host "1) Ejecutar Scraper"
    Write-Host "2) Test Run"
    Write-Host "3) Ejecutar Headless"
    Write-Host "4) AI Helper"
    Write-Host "5) Scraper Sillas Gamer"
    Write-Host ""
    Write-Host "6) Instalar/Reinstalar Dependencias"
    Write-Host "7) Reinstalar Playwright"
    Write-Host "8) Recrear Entorno Virtual"
    Write-Host ""
    Write-Host "0) Salir"
    Write-Host ""

    $opcion = Read-Host "Seleccione una opción"

    switch ($opcion)
    {
        "1"
        {
            python main.py
            Pause
        }

        "2"
        {
            python main.py --test-run
            Pause
        }

        "3"
        {
            python main.py --headless
            Pause
        }

        "4"
        {
            python ai_helper.py
            Pause
        }

        "5"
        {
            python chairs_scraper.py --headless
            Pause
        }

        "6"
        {
            pip install -r requirements.txt
            Pause
        }

        "7"
        {
            playwright install chromium
            Pause
        }

        "8"
        {
            deactivate 2>$null

            Remove-Item venv -Recurse -Force

            python -m venv venv

            . .\venv\Scripts\Activate.ps1

            pip install -r requirements.txt

            playwright install chromium

            Pause
        }

        "0"
        {
            exit
        }

        default
        {
            Write-Host ""
            Write-Host "Opción inválida." -ForegroundColor Red
            Pause
        }
    }
}

function Pause
{
    Write-Host ""
    Read-Host "Presione ENTER para regresar al menú"
}
