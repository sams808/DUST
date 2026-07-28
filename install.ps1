<#
.SYNOPSIS
    First-time setup for DUST: checks Python 3.11, installs dependencies,
    generates brand assets, and writes the DUST.bat launcher.
.USAGE
    Right-click -> Run with PowerShell, or:  powershell -ExecutionPolicy Bypass -File install.ps1
#>

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Output "== DUST install =="

# 1. Python 3.11 via the 'py' launcher (plain 'python' can resolve to a
#    different / dependency-less install on this kind of machine).
try {
    $pyVersion = & py -3.11 --version 2>&1
    Write-Output "Found: $pyVersion"
} catch {
    Write-Error "Python 3.11 was not found via the 'py' launcher. Install it from https://www.python.org/downloads/ (make sure 'py launcher' is included), then re-run this script."
    exit 1
}

# 2. Dependencies
Write-Output "Installing dependencies from requirements.txt..."
& py -3.11 -m pip install --upgrade pip
& py -3.11 -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install failed - see output above."
    exit 1
}

# 3. Brand assets (logo / splash / icon)
Write-Output "Generating brand assets..."
& py -3.11 (Join-Path $PSScriptRoot "make_logo.py")

# 4. Launcher .bat (kept in sync with the template used by update.ps1)
$batPath = Join-Path $PSScriptRoot "DUST.bat"
$batContent = @'
@echo off
rem Double-click launcher for DUST.
rem Uses the Windows py launcher to pick Python 3.11 explicitly.
rem Starts windowless (pyw); if that fails, falls back to a visible
rem console run so any error is readable instead of silently vanishing.
cd /d "%~dp0"

where pyw >nul 2>nul
if errorlevel 1 goto :console

start "" pyw -3.11 app.py
exit /b 0

:console
py -3.11 app.py
if errorlevel 1 pause
'@
Set-Content -Path $batPath -Value $batContent -Encoding ascii
Write-Output "Wrote launcher: $batPath"

Write-Output ""
Write-Output "Install complete. Run DUST.bat (or 'py -3.11 app.py') to start the app."
