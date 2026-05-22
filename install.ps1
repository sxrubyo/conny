Write-Host "✦ Conny AI - Python Native Installer (Windows)" -ForegroundColor Magenta
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray

# 1. Check Python
if (-Not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python no está instalado o no está en el PATH." -ForegroundColor Red
    exit 1
}

$InstallDir = "$HOME\.conny-app"
if (Test-Path $InstallDir) {
    Write-Host "Limpiando instalación anterior..." -ForegroundColor DarkGray
    Remove-Item -Recurse -Force $InstallDir
}

Write-Host "1. Clonando repositorio desde GitHub..." -ForegroundColor Cyan
git clone -b refactor-v10 https://github.com/sxrubyo/conny.git $InstallDir | Out-Null

Set-Location $InstallDir

Write-Host "2. Creando entorno virtual aislado de Python..." -ForegroundColor Cyan
python -m venv .venv

Write-Host "3. Instalando dependencias de IA..." -ForegroundColor Cyan
& ".\.venv\Scripts\pip.exe" install -r requirements.txt deep-translator | Out-Null

Write-Host "4. Creando atajo global 'conny'..." -ForegroundColor Cyan
$ProfilePath = if (Test-Path $PROFILE) { $PROFILE } else { New-Item -ItemType File -Path $PROFILE -Force }
$AliasCmd = "function conny { & `"$InstallDir\.venv\Scripts\python.exe`" `"$InstallDir\conny_cli.py`" `$args }"
Add-Content -Path $ProfilePath -Value $AliasCmd

Write-Host ""
Write-Host "✔ ¡Instalación pura en Python completada exitosamente!" -ForegroundColor Green
Write-Host "Reinicia esta consola de PowerShell y ejecuta: " -NoNewline
Write-Host "conny init" -ForegroundColor Magenta
Write-Host ""
