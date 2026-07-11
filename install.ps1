Write-Host "✦ Bublee AI - Python Native Installer (Windows)" -ForegroundColor Magenta
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray

# 1. Check Python robustly
$PythonCmd = $null
foreach ($cmd in @("py", "python3", "python")) {
    try {
        $out = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $?) {
            $PythonCmd = $cmd
            break
        }
    } catch {}
}

if (-Not $PythonCmd) {
    Write-Host "Error: Python no está instalado o no está configurado en tu PATH. Descárgalo de python.org" -ForegroundColor Red
    exit 1
}

$InstallDir = "$HOME\.bublee-app"
if (Test-Path $InstallDir) {
    Write-Host "Limpiando instalación anterior..." -ForegroundColor DarkGray
    Remove-Item -Recurse -Force $InstallDir
}

Write-Host "1. Clonando repositorio desde GitHub..." -ForegroundColor Cyan
git clone -b refactor-v10 https://github.com/sxrubyo/bublee.git $InstallDir | Out-Null

Set-Location $InstallDir

Write-Host "2. Creando entorno virtual aislado de Python con '$PythonCmd'..." -ForegroundColor Cyan
try {
    & $PythonCmd -m venv .venv
} catch {
    Write-Host "Error al crear el entorno virtual. Revisa tu instalación de Python." -ForegroundColor Red
    exit 1
}

Write-Host "3. Instalando dependencias de IA..." -ForegroundColor Cyan
if (Test-Path ".\.venv\Scripts\pip.exe") {
    & ".\.venv\Scripts\pip.exe" install -r requirements.txt deep-translator | Out-Null
} else {
    Write-Host "Error: No se encontró pip en el entorno virtual." -ForegroundColor Red
    exit 1
}

Write-Host "4. Creando atajo global 'bublee'..." -ForegroundColor Cyan
$ProfilePath = if (Test-Path $PROFILE) { $PROFILE } else { New-Item -ItemType File -Path $PROFILE -Force }
$AliasCmd = "function bublee { & `"$InstallDir\.venv\Scripts\python.exe`" `"$InstallDir\bublee_cli.py`" `$args }"
Add-Content -Path $ProfilePath -Value $AliasCmd

Write-Host ""
Write-Host "✔ ¡Instalación pura en Python completada exitosamente!" -ForegroundColor Green
Write-Host "Reinicia esta consola de PowerShell y ejecuta: " -NoNewline
Write-Host "bublee init" -ForegroundColor Magenta
Write-Host ""
